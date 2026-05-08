from qrisp import QuantumArray, QuantumBool, QuantumFloat, QuantumVariable, dicke_state, x, cx, control, swap, auto_uncompute
import math

class ISDInfo:
    def __init__(self, n, k, good_column_choices, matrix):
        self.n = n
        self.k = k
        self.good_column_choices = good_column_choices
        self.matrix = matrix

class ISD:
    def print_matrix(self, matrix, title):
        print(f"{title}:")
        for row in matrix:
            # Convert all values to string representations of integers
            r = [str(int(val)) for val in row]
            
            # Print with a pipe before the last element, handling cases where the row might be empty or have 1 element
            if len(r) > 1:
                print(f"{' '.join(r[:-1])} | {r[-1]}")
            elif len(r) == 1:
                print(r[0])
            else:
                print()
        print()

    @auto_uncompute
    def apply_optimisation(self, B, q_matrix, X, n, k):
        c = QuantumFloat((n - k).bit_length())
        c[:] = n - k

        for i in range(n - k):
            for j in range(i):
                with control(B[i]):
                    with c == n - k - j:
                        swap(q_matrix[i], q_matrix[j])

            with control(B[i]):
                c -= 1

        for i in range(k - 1, -1, -1):
            with control(B[n - k + i]):
                c -= 1
                x(X[i])
                for j in range(i, k - 1):
                    swap(q_matrix[:,j], q_matrix[:,j + 1])
                    swap(X[j], X[j + 1])

    @auto_uncompute
    def controlled_solve(self, q_matrix, X, dim, all_columns):
        offset = max(all_columns - dim, 0)
        start_column = max(dim - all_columns, 0)

        for i in range(start_column, dim - 1):
            with control(X[i + offset - start_column][0]):
                # pivot search
                for j in range(i + 1, dim):
                    # controls = q_matrix[i + offset - start_column, i:j]
                    # controls = q_matrix[i:j, i + offset - start_column]
                    controls = [q_matrix[k, i + offset - start_column][0] for k in range(i, j)]

                    x(controls)

                    # with control([qb[0] for qb in controls]):
                    with control(controls):
                        for col in range(i + 1, dim + 1):
                            cx(q_matrix[j, col + offset - start_column], q_matrix[i, col + offset - start_column])

                    x(controls)

                # row reduce
                for j in range(i + 1, dim):
                    with control(q_matrix[j, i + offset - start_column]):
                        #for col in range(i + 1, dim + 1):
                        for col in range(i + 1, dim + 1):
                            cx(q_matrix[i, col + offset - start_column], q_matrix[j, col + offset - start_column])

        # back substitution
        for i in range(dim - 1, max(0, start_column - 1), -1):
            with control(X[i + offset - start_column][0]) :
                for j in range(i - 1, -1, -1):
                    with control(q_matrix[j, i + offset - start_column]):
                        cx(q_matrix[i, dim + offset - start_column], q_matrix[j, dim + offset - start_column])

    def get_big_info(self):
        n = 7
        k = 4
        q_matrix = QuantumArray(qtype=QuantumBool(), shape=(n - k, k + 1))

        classical_matrix = [
            [1, 0, 1, 1, 1],
            [1, 1, 0, 1, 1],
            [0, 1, 1, 1, 0]
        ]

        q_matrix[:] = classical_matrix

        good_column_choices = [13, 14, 25, 26, 28, 41, 42, 44, 73, 74, 88, 104]

        return ISDInfo(n, k, good_column_choices, q_matrix)

    def run_big(self):
        q_matrix = QuantumArray(qtype=QuantumBool(), shape=(3, 5))

        classical_matrix = [
            [1, 0, 1, 1, 1],
            [1, 1, 0, 1, 1],
            [0, 1, 1, 1, 0]
        ]

        q_matrix[:] = classical_matrix
        print("======================= ISD ======================")

        self.print_matrix(classical_matrix, "Input matrix")

        n = 7
        k = 4

        X = QuantumArray(qtype=QuantumBool(), shape=(k,))

        B = QuantumVariable(n)
        x(B[k:])
        dicke_state(B, n - k)

        self.apply_optimisation(B, q_matrix, X, n, k)
        self.controlled_solve(q_matrix, X, n - k, k)

        res = q_matrix.get_measurement()
        print("Weight distribution:")
        weight_distribution = {}

        for matrix_state, prob in res.items():
            # matrix_state is typically a tuple of tuples representing rows
            # Example: ((1, 2), (3, 4)) -> a 2x2 matrix
            
            # Grab the last element (column) from each row and sum them up
            last_col_sum = sum(row[-1] for row in matrix_state)
            
            # Accumulate the probabilities for this specific sum
            if last_col_sum in weight_distribution:
                weight_distribution[last_col_sum] += prob
            else:
                weight_distribution[last_col_sum] = prob

        # Sort by the sum and print as percentages
        print("Sum of Last Column -> Percentage")
        print("-" * 32)
        for total, prob in sorted(weight_distribution.items()):
            percentage = prob * 100
            print(f"Sum: {total:<5} -> {percentage:.2f}%")  

        # final_state = max(res, key=res.get)
        # self.print_matrix(final_state, "Output matrix")

    def get_ok_info(self):
        n = 6
        k = 3
        q_matrix = QuantumArray(qtype=QuantumBool(), shape=(n - k, k + 1))

        classical_matrix = [
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ]

        q_matrix[:] = classical_matrix

        good_column_choices = [13, 14, 25, 26, 28, 41, 42, 44]

        return ISDInfo(n, k, good_column_choices, q_matrix)

    def run_ok(self):
        q_matrix = QuantumArray(qtype=QuantumBool(), shape=(3, 4))

        classical_matrix = [
            [0, 1, 1, 0],
            [1, 0, 1, 0],
            [1, 1, 0, 1]
        ]

        q_matrix[:] = classical_matrix
        print("======================= ISD ======================")

        self.print_matrix(classical_matrix, "Input matrix")

        n = 6
        k = 3

        X = QuantumArray(qtype=QuantumBool(), shape=(k,))

        B = QuantumVariable(n)
        x(B[k:])
        dicke_state(B, n - k)

        self.apply_optimisation(B, q_matrix, X, n, k)
        self.controlled_solve(q_matrix, X, n - k, k)

        res = q_matrix.get_measurement()
        print("Weight distribution:")
        weight_distribution = {}

        for matrix_state, prob in res.items():
            # matrix_state is typically a tuple of tuples representing rows
            # Example: ((1, 2), (3, 4)) -> a 2x2 matrix
            
            # Grab the last element (column) from each row and sum them up
            last_col_sum = sum(row[-1] for row in matrix_state)
            
            # Accumulate the probabilities for this specific sum
            if last_col_sum in weight_distribution:
                weight_distribution[last_col_sum] += prob
            else:
                weight_distribution[last_col_sum] = prob

        # Sort by the sum and print as percentages
        print("Sum of Last Column -> Percentage")
        print("-" * 32)
        for total, prob in sorted(weight_distribution.items()):
            percentage = prob * 100
            print(f"Sum: {total:<5} -> {percentage:.2f}%")  

        # final_state = max(res, key=res.get)
        # self.print_matrix(final_state, "Output matrix")

    def get_smol_info(self):
        n = 5
        k = 2
        q_matrix = QuantumArray(qtype=QuantumBool(), shape=(n - k, k + 1))

        classical_matrix = [
            [1, 1, 1],
            [1, 1, 1],
            [0, 1, 0]
        ]

        q_matrix[:] = classical_matrix

        good_column_choices = [13, 14, 25, 26]

        return ISDInfo(n, k, good_column_choices, q_matrix)

    # def run_smol(self):
    #     smol_info = self.get_smol_info()

    #     run_superposition_solver()

    #     # q_matrix = QuantumArray(qtype=QuantumBool(), shape=(3, 3))

    #     # classical_matrix = [
    #     #     [1, 1, 1],
    #     #     [1, 1, 1],
    #     #     [0, 1, 0]
    #     # ]

    #     # q_matrix[:] = classical_matrix
    #     # print("======================= ISD ======================")

    #     # #self.print_matrix(classical_matrix, "Input matrix")

    #     # n = 5
    #     # k = 2

    #     # X = QuantumArray(qtype=QuantumBool(), shape=(k,))

    #     # B = QuantumVariable(n)
    #     # x(B[k:])
    #     # dicke_state(B, n - k)

    #     # self.apply_optimisation(B, q_matrix, X, n, k)
    #     # self.controlled_solve(q_matrix, X, n - k, k)

    #     # res = q_matrix.get_measurement()
    #     # print("Weight distribution:")
    #     # weight_distribution = {}

    #     # for matrix_state, prob in res.items():
    #     #     # matrix_state is typically a tuple of tuples representing rows
    #     #     # Example: ((1, 2), (3, 4)) -> a 2x2 matrix
            
    #     #     # Grab the last element (column) from each row and sum them up
    #     #     last_col_sum = sum(row[-1] for row in matrix_state)
            
    #     #     # Accumulate the probabilities for this specific sum
    #     #     if last_col_sum in weight_distribution:
    #     #         weight_distribution[last_col_sum] += prob
    #     #     else:
    #     #         weight_distribution[last_col_sum] = prob

    #     # # Sort by the sum and print as percentages
    #     # print("Sum of Last Column -> Percentage")
    #     # print("-" * 32)
    #     # for total, prob in sorted(weight_distribution.items()):
    #     #     percentage = prob * 100
    #     #     print(f"Sum: {total:<5} -> {percentage:.2f}%")  

    #     # # final_state = max(res, key=res.get)
    #     # # self.print_matrix(final_state, "Output matrix")

    def run_examples(self):
        self.run_superposition_solver(self.get_smol_info())
        self.run_superposition_solver(self.get_ok_info())
        self.run_superposition_solver(self.get_big_info())


    def run_all(self):
        for mask in range(1 << 5):
            if mask.bit_count() == 3:
                print(f"Decimal: {mask:2} | Binary: {mask:05b}")

                q_matrix = QuantumArray(qtype=QuantumBool(), shape=(3, 3))

                classical_matrix = [
                    [1, 1, 1],
                    [1, 1, 1],
                    [0, 1, 0]
                ]

                q_matrix[:] = classical_matrix
                n = 5
                k = 2

                X = QuantumArray(qtype=QuantumBool(), shape=(k,))

                B = QuantumVariable(n)

                for i in range(len(B)):
                    if (mask >> i) & 1:
                        x(B[i]) 


                self.apply_optimisation(B, q_matrix, X, n, k)
                self.controlled_solve(q_matrix, X, n - k, k)

                res = q_matrix.get_measurement()

                final_state = max(res, key=res.get)
                self.print_matrix(final_state, "Output matrix")

    def run_superposition_solver(self, isd_info):
        n = isd_info.n
        k = isd_info.k
        matrix = isd_info.matrix
        self.print_matrix(matrix, "Running superposition solver for:")
        print(f"Expected probability of weight one: {isd_info.good_column_choices.size() / math.comb(n, n - k)}")

        X = QuantumArray(qtype=QuantumBool(), shape=(k,))

        B = QuantumVariable(n)
        x(B[k:])
        dicke_state(B, n - k)

        self.apply_optimisation(B, matrix, X, n, k)
        self.controlled_solve(matrix, X, n - k, k)

        res = matrix.get_measurement()
        print("Weight distribution:")
        weight_distribution = {}

        for matrix_state, prob in res.items():
            last_col_sum = sum(row[-1] for row in matrix_state)
            
            if last_col_sum in weight_distribution:
                weight_distribution[last_col_sum] += prob
            else:
                weight_distribution[last_col_sum] = prob

        for total, prob in sorted(weight_distribution.items()):
            percentage = prob * 100
            print(f"Sum: {total:<5} -> {percentage:.2f}%")  



isd = ISD()
isd.run_examples()