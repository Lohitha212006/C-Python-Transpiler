// test5_logic.mc  - logical operators, nested conditions
int classify(int x) {
    if (x > 0 && x < 10) {
        return 1;
    } else {
        if (x >= 10) {
            return 2;
        } else {
            return 0;
        }
    }
}

int main() {
    int a = classify(5);
    int b = classify(15);
    int c = classify(-3);
    return a;
}
