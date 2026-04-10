#include <iostream>
#include <string>

int add(int a, int b) {
    return a + b;
}

int multiply(int x, int y) {
    int result = 0;
    for (int i = 0; i < y; i++) {
        result = add(result, x);
    }
    return result;
}

void print_result(int value) {
    std::cout << "Result: " << value << std::endl;
}

int main() {
    int a = 5, b = 3;
    int sum = add(a, b);
    int product = multiply(sum, 2);
    print_result(product);
    return 0;
}