// test4_functions.mc  - multiple functions, function calls
int factorial(int n) {
    if (n <= 1) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}

int add(int a, int b) {
    return a + b;
}

int main() {
    int f = factorial(5);
    int s = add(f, 10);
    return s;
}
