#pragma once

// Bounded persistent workers for independent, immutable-input numerical rows.
// A call is a barrier: no caller may inspect or swap output before it returns.
// No numerical reduction is reordered here; boundary/face audits stay serial.
#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <cfenv>
#include <exception>
#include <functional>
#include <mutex>
#include <thread>
#include <vector>
#include <stdexcept>
#if defined(_M_X64) || defined(__SSE__)
#include <xmmintrin.h>
#endif

namespace raftsim::solver_detail {

// 0 means the unchanged default; bit 7 seals configuration once the shared pool
// starts. Compare/exchange makes configuration versus first use race-safe.
inline std::atomic<unsigned> solver_worker_configuration{0};
inline void configure_solver_worker_limit(unsigned lanes) {
    if (lanes == 0 || lanes > 64) throw std::invalid_argument("Solver worker limit must be in [1,64].");
    unsigned expected=0;
    if (!solver_worker_configuration.compare_exchange_strong(expected,lanes))
        throw std::logic_error("Solver worker limit must be configured once before first use.");
}
inline unsigned take_solver_worker_limit() {
    // Retain the requested limit if static initialization retries after a
    // thread-construction exception; it must not turn the seal into a count.
    const unsigned value=solver_worker_configuration.fetch_or(128u)&127u;
    return value == 0 ? 4u : value;
}

class SolverRowExecutor {
public:
    using Task = std::function<void(std::size_t, std::size_t)>;
    explicit SolverRowExecutor(unsigned requested_lanes=4u) {
        if (requested_lanes == 0 || requested_lanes > 64)
            throw std::invalid_argument("Solver worker limit must be in [1,64].");
        const unsigned count = std::min(requested_lanes, std::max(1u, std::thread::hardware_concurrency()));
        try {
            for (unsigned i = 1; i < count; ++i)
                workers_.emplace_back([this] { worker(); });
        } catch (...) {
            {
                std::lock_guard<std::mutex> lock(state_mutex_);
                stopping_ = true;
            }
            ready_.notify_all();
            for (auto& worker : workers_) worker.join();
            throw;
        }
    }
    ~SolverRowExecutor() { shutdown(); }
    void shutdown() {
        std::lock_guard<std::mutex> dispatch(dispatch_mutex_);
        {
            std::lock_guard<std::mutex> lock(state_mutex_);
            stopping_ = true;
        }
        ready_.notify_all();
        for (auto& worker : workers_) worker.join();
        workers_.clear();
    }
    SolverRowExecutor(const SolverRowExecutor&) = delete;
    SolverRowExecutor& operator=(const SolverRowExecutor&) = delete;

    void run(std::size_t rows, const Task& task) {
        if (executing_) { task(0, rows); return; }
        // Multiple solver instances cannot overwrite an in-flight dispatch.
        std::unique_lock<std::mutex> dispatch(dispatch_mutex_);
        if (workers_.empty()) { dispatch.unlock(); task(0, rows); return; }
        {
            std::lock_guard<std::mutex> lock(state_mutex_);
            task_ = task;
            rows_ = rows;
            next_.store(0, std::memory_order_relaxed);
            failure_ = nullptr;
            // A host can select denormal/rounding behavior on its game thread.
            // Persistent workers must use that same environment for this step.
            std::fegetenv(&environment_);
#if defined(_M_X64) || defined(__SSE__)
            mxcsr_ = _mm_getcsr();
#endif
            pending_ = workers_.size();
            ++generation_;
        }
        ready_.notify_all();
        execute_chunks();
        std::unique_lock<std::mutex> lock(state_mutex_);
        finished_.wait(lock, [this] { return pending_ == 0; });
        task_ = {};
        if (failure_) std::rethrow_exception(failure_);
    }

private:
    void execute_chunks() {
        std::fenv_t previous_environment;
        std::fegetenv(&previous_environment);
#if defined(_M_X64) || defined(__SSE__)
        const unsigned previous_mxcsr = _mm_getcsr();
#endif
        std::fesetenv(&environment_);
#if defined(_M_X64) || defined(__SSE__)
        _mm_setcsr(mxcsr_);
#endif
        executing_ = true;
        try {
            for (;;) {
                const auto first = next_.fetch_add(8, std::memory_order_relaxed);
                if (first >= rows_) break;
                task_(first, std::min(first + 8, rows_));
            }
        } catch (...) {
            std::lock_guard<std::mutex> lock(state_mutex_);
            if (!failure_) failure_ = std::current_exception();
        }
        executing_ = false;
        std::fesetenv(&previous_environment);
#if defined(_M_X64) || defined(__SSE__)
        _mm_setcsr(previous_mxcsr);
#endif
    }
    void worker() {
        std::size_t seen = 0;
        for (;;) {
            std::unique_lock<std::mutex> lock(state_mutex_);
            ready_.wait(lock, [this, seen] { return stopping_ || generation_ != seen; });
            if (stopping_) return;
            seen = generation_;
            lock.unlock();
            execute_chunks();
            lock.lock();
            if (--pending_ == 0) finished_.notify_one();
        }
    }
    inline static thread_local bool executing_ = false;
    std::vector<std::thread> workers_;
    std::mutex dispatch_mutex_, state_mutex_;
    std::condition_variable ready_, finished_;
    std::atomic<std::size_t> next_{0};
    std::size_t rows_ = 0, generation_ = 0, pending_ = 0;
    bool stopping_ = false;
    Task task_;
    std::fenv_t environment_{};
#if defined(_M_X64) || defined(__SSE__)
    unsigned mxcsr_ = 0;
#endif
    std::exception_ptr failure_;
};

inline SolverRowExecutor& solver_row_executor() {
    static SolverRowExecutor executor(take_solver_worker_limit());
    return executor;
}

inline void solver_row_ranges(std::size_t rows, bool parallel, const SolverRowExecutor::Task& task) {
    if (!parallel || rows < 16) { task(0, rows); return; }
    solver_row_executor().run(rows, task);
}

} // namespace raftsim::solver_detail
