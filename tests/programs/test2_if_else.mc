// test2_if_else.mc  - if / else branches
int max(int x, int y) {
    if (x > y) {
        return x;
    } else {
        return y;
    }
}

int main() {
    int result = max(5, 9);
    return result;
}
