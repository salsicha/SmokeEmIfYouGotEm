#include <chrono/physics/ChSystemSMC.h>

#include <exception>
#include <iostream>

int main() {
    try {
        chrono::ChSystemSMC system;
        constexpr double fixed_dt = 1.0 / 120.0;
        system.DoStepDynamics(fixed_dt);
        std::cout << "chrono_smoke=ok\n";
        std::cout << "fixed_dt=" << fixed_dt << "\n";
        std::cout << "time=" << system.GetChTime() << "\n";
        return 0;
    } catch (const std::exception& exc) {
        std::cerr << "chrono_smoke=failed\n";
        std::cerr << "error=" << exc.what() << "\n";
        return 1;
    }
}
