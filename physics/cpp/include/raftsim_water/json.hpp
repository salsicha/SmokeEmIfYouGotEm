#pragma once

#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace raftsim {

class JsonValue {
public:
    using Array = std::vector<JsonValue>;
    using Object = std::map<std::string, JsonValue>;
    using Storage = std::variant<std::nullptr_t, bool, double, std::string, Array, Object>;

    JsonValue() = default;
    explicit JsonValue(std::nullptr_t) : value_(nullptr) {}
    explicit JsonValue(bool value) : value_(value) {}
    explicit JsonValue(double value) : value_(value) {}
    explicit JsonValue(std::string value) : value_(std::move(value)) {}
    explicit JsonValue(Array value) : value_(std::move(value)) {}
    explicit JsonValue(Object value) : value_(std::move(value)) {}

    bool is_null() const { return std::holds_alternative<std::nullptr_t>(value_); }
    bool is_bool() const { return std::holds_alternative<bool>(value_); }
    bool is_number() const { return std::holds_alternative<double>(value_); }
    bool is_string() const { return std::holds_alternative<std::string>(value_); }
    bool is_array() const { return std::holds_alternative<Array>(value_); }
    bool is_object() const { return std::holds_alternative<Object>(value_); }

    bool as_bool() const;
    double as_number() const;
    int as_int() const;
    const std::string& as_string() const;
    const Array& as_array() const;
    const Object& as_object() const;

    const JsonValue& at(const std::string& key) const;
    const JsonValue& at(std::size_t index) const;
    const JsonValue* find(const std::string& key) const;

    std::string string_or(const std::string& key, const std::string& fallback) const;
    double number_or(const std::string& key, double fallback) const;
    int int_or(const std::string& key, int fallback) const;

private:
    Storage value_ = nullptr;
};

JsonValue parse_json(const std::string& text);
JsonValue parse_json_file(const std::string& path);

}  // namespace raftsim
