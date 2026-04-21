// test3_while.mc  - while loop with accumulator
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
    int s = sum_to(10);
    return s;
}
