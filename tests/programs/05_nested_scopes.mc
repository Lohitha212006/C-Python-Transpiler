// Test 5: Nested scopes and variable shadowing
int compute(int n) {
    int result = 0;
    int i = 0;
    while (i < n) {
        int temp = i * i;
        result = result + temp;
        i = i + 1;
    }
    return result;
}

int main() {
    int val = compute(5);
    return val;
}
