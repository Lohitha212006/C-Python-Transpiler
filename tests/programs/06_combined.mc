// Test 6: Combined program (fibonacci)
int fib(int n) {
    if (n <= 1) {
        return n;
    }
    int a = fib(n - 1);
    int b = fib(n - 2);
    return a + b;
}

int main() {
    int result = fib(8);
    return result;
}
