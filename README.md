# Maple-IDAT User Guide

## 1. Following the [Maple User Guide](https://github.com/jieyu/maple) to build the branch Maple-IDAT.
## 2. Three Approaches for Testing Multi-threaded Programs based on Maple:

* Running Maple with multiple random test inputs:

    $ <maple_home>/script/idiom my_rand_gen_10 --- <absolute_path_to_the_executable_under_test>

* Input-Driven Active Testing with Test Selection Strategy I

    $ <maple_home>/script/idiom my_test_gen_10 --- <absolute_path_to_the_executable_under_test>

* Input-Driven Active Testing with Test Selection Stratefy II

    $ <maple_home>/script/idiom my_test_genp_10 --- <absolute_path_to_the_executable_under_test>
