## Maple-IDAT User Guide

### Build
Please follow the [Maple User Guide](https://github.com/jieyu/maple) to build the branch Maple-IDAT.
### Configuration in <maple_home>/script/maple/idiom/main.py
    |_is_update_memo            | enable the memoization option in Maple
    |_is_fatal                  | detect only the first concurrency bug
    |_num_of_candidate_testcase | initial number of candidate test inputs
    |_rand_upper                | upper bound of a random integer
    |_rand_lower                | lower bound of a random integer
### Three Approaches for Testing Multi-threaded Programs based on Maple:
#### Maple: Running Maple with multiple random test inputs:
        $ <maple_home>/script/idiom my_rand_gen_10 --- <absolute_path_to_the_executable_under_test>
#### IDAT-I: Input-Driven Active Testing with Test Selection Strategy I
        $ <maple_home>/script/idiom my_test_gen_10 --- <absolute_path_to_the_executable_under_test>
#### IDAT-II: Input-Driven Active Testing with Test Selection Strategy II
        $ <maple_home>/script/idiom my_test_genp_10 --- <absolute_path_to_the_executable_under_test>
#### SPLASH-2 by IDAT-II
        $ <maple_home>/script/idiom my_test_pro_10 --- <absolute_path_to_the_SPLASH2_executable_under_test>
