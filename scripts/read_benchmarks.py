import pathlib
import glom


def main():
    benchmarks = read_bencmarks(".benchmarks")

    grouped = group_tests()
