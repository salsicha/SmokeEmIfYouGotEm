#include "raftsim_water/json.hpp"

#include <cctype>
#include <cmath>
#include <fstream>
#include <sstream>

namespace raftsim {

namespace {

class JsonParser {
public:
    explicit JsonParser(const std::string& text) : text_(text) {}

    JsonValue parse() {
        skip_ws();
        JsonValue value = parse_value();
        skip_ws();
        if (pos_ != text_.size()) {
            throw std::runtime_error("Unexpected trailing JSON content.");
        }
        return value;
    }

private:
    const std::string& text_;
    std::size_t pos_ = 0;

    void skip_ws() {
        while (pos_ < text_.size() && std::isspace(static_cast<unsigned char>(text_[pos_]))) {
            ++pos_;
        }
    }

    char peek() const {
        if (pos_ >= text_.size()) {
            throw std::runtime_error("Unexpected end of JSON.");
        }
        return text_[pos_];
    }

    char get() {
        char c = peek();
        ++pos_;
        return c;
    }

    void expect(char expected) {
        char actual = get();
        if (actual != expected) {
            throw std::runtime_error(std::string("Expected JSON character '") + expected + "' but found '" + actual + "'.");
        }
    }

    bool consume_literal(const std::string& literal) {
        if (text_.compare(pos_, literal.size(), literal) == 0) {
            pos_ += literal.size();
            return true;
        }
        return false;
    }

    JsonValue parse_value() {
        skip_ws();
        char c = peek();
        if (c == '"') {
            return JsonValue(parse_string());
        }
        if (c == '{') {
            return JsonValue(parse_object());
        }
        if (c == '[') {
            return JsonValue(parse_array());
        }
        if (c == '-' || std::isdigit(static_cast<unsigned char>(c))) {
            return JsonValue(parse_number());
        }
        if (consume_literal("true")) {
            return JsonValue(true);
        }
        if (consume_literal("false")) {
            return JsonValue(false);
        }
        if (consume_literal("null")) {
            return JsonValue(nullptr);
        }
        throw std::runtime_error("Invalid JSON value.");
    }

    JsonValue::Object parse_object() {
        JsonValue::Object object;
        expect('{');
        skip_ws();
        if (peek() == '}') {
            get();
            return object;
        }
        while (true) {
            skip_ws();
            std::string key = parse_string();
            skip_ws();
            expect(':');
            object.emplace(std::move(key), parse_value());
            skip_ws();
            char c = get();
            if (c == '}') {
                break;
            }
            if (c != ',') {
                throw std::runtime_error("Expected ',' or '}' in JSON object.");
            }
        }
        return object;
    }

    JsonValue::Array parse_array() {
        JsonValue::Array array;
        expect('[');
        skip_ws();
        if (peek() == ']') {
            get();
            return array;
        }
        while (true) {
            array.push_back(parse_value());
            skip_ws();
            char c = get();
            if (c == ']') {
                break;
            }
            if (c != ',') {
                throw std::runtime_error("Expected ',' or ']' in JSON array.");
            }
        }
        return array;
    }

    std::string parse_string() {
        expect('"');
        std::string result;
        while (true) {
            char c = get();
            if (c == '"') {
                break;
            }
            if (c == '\\') {
                char escaped = get();
                switch (escaped) {
                    case '"':
                    case '\\':
                    case '/':
                        result.push_back(escaped);
                        break;
                    case 'b':
                        result.push_back('\b');
                        break;
                    case 'f':
                        result.push_back('\f');
                        break;
                    case 'n':
                        result.push_back('\n');
                        break;
                    case 'r':
                        result.push_back('\r');
                        break;
                    case 't':
                        result.push_back('\t');
                        break;
                    default:
                        throw std::runtime_error("Unsupported JSON escape sequence.");
                }
            } else {
                result.push_back(c);
            }
        }
        return result;
    }

    double parse_number() {
        std::size_t start = pos_;
        if (peek() == '-') {
            ++pos_;
        }
        while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) {
            ++pos_;
        }
        if (pos_ < text_.size() && text_[pos_] == '.') {
            ++pos_;
            while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) {
                ++pos_;
            }
        }
        if (pos_ < text_.size() && (text_[pos_] == 'e' || text_[pos_] == 'E')) {
            ++pos_;
            if (pos_ < text_.size() && (text_[pos_] == '+' || text_[pos_] == '-')) {
                ++pos_;
            }
            while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) {
                ++pos_;
            }
        }
        return std::stod(text_.substr(start, pos_ - start));
    }
};

}  // namespace

bool JsonValue::as_bool() const {
    if (!is_bool()) {
        throw std::runtime_error("JSON value is not a boolean.");
    }
    return std::get<bool>(value_);
}

double JsonValue::as_number() const {
    if (!is_number()) {
        throw std::runtime_error("JSON value is not a number.");
    }
    return std::get<double>(value_);
}

int JsonValue::as_int() const {
    return static_cast<int>(std::lround(as_number()));
}

const std::string& JsonValue::as_string() const {
    if (!is_string()) {
        throw std::runtime_error("JSON value is not a string.");
    }
    return std::get<std::string>(value_);
}

const JsonValue::Array& JsonValue::as_array() const {
    if (!is_array()) {
        throw std::runtime_error("JSON value is not an array.");
    }
    return std::get<Array>(value_);
}

const JsonValue::Object& JsonValue::as_object() const {
    if (!is_object()) {
        throw std::runtime_error("JSON value is not an object.");
    }
    return std::get<Object>(value_);
}

const JsonValue& JsonValue::at(const std::string& key) const {
    const auto& object = as_object();
    auto it = object.find(key);
    if (it == object.end()) {
        throw std::runtime_error("Missing JSON object key: " + key);
    }
    return it->second;
}

const JsonValue& JsonValue::at(std::size_t index) const {
    const auto& array = as_array();
    if (index >= array.size()) {
        throw std::runtime_error("JSON array index out of range.");
    }
    return array[index];
}

const JsonValue* JsonValue::find(const std::string& key) const {
    if (!is_object()) {
        return nullptr;
    }
    const auto& object = as_object();
    auto it = object.find(key);
    return it == object.end() ? nullptr : &it->second;
}

std::string JsonValue::string_or(const std::string& key, const std::string& fallback) const {
    const JsonValue* value = find(key);
    if (value == nullptr || value->is_null()) {
        return fallback;
    }
    return value->as_string();
}

double JsonValue::number_or(const std::string& key, double fallback) const {
    const JsonValue* value = find(key);
    if (value == nullptr || value->is_null()) {
        return fallback;
    }
    return value->as_number();
}

int JsonValue::int_or(const std::string& key, int fallback) const {
    const JsonValue* value = find(key);
    if (value == nullptr || value->is_null()) {
        return fallback;
    }
    return value->as_int();
}

JsonValue parse_json(const std::string& text) {
    return JsonParser(text).parse();
}

JsonValue parse_json_file(const std::string& path) {
    std::ifstream stream(path);
    if (!stream) {
        throw std::runtime_error("Could not open JSON file: " + path);
    }
    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return parse_json(buffer.str());
}

}  // namespace raftsim

