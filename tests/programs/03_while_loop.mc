// Test 3: While loop
int sum_to(int n) {
    int total = 0;
    int i = 1;
    while (i <= n) {
        total = total + i;
        i = i + 1;
    }
    return total;
}

int main() {
    int result = sum_to(10);
    return result;
}
