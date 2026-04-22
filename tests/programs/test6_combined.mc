// test6_combined.mc  - floats, combined constructs
float average(float a, float b) {
    float sum = a + b;
    return sum;
}

int count_down(int n) {
    int result = 0;
    while (n > 0) {
        result = result + n;
        n = n - 1;
    }
    return result;
}

int main() {
    float avg = average(4.0, 6.0);
    int cd = count_down(5);
    return cd;
}
