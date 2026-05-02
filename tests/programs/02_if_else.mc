// Test 2: If-else branching
int abs_val(int x) {
    if (x < 0) {
        return 0 - x;
    } else {
        return x;
    }
}

int main() {
    int a = abs_val(5);      // 5
    int b = abs_val(0 - 7);  // 7
    return a + b;            // 12
}
