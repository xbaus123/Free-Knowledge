int max_of(const int *xs, int n) {
    int best = xs[0];
    for (int i = 1; i < n; i++) {
        if (xs[i] > best) best = xs[i];
    }
    return best;
}
