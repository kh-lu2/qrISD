from qrisp import QuantumArray, QuantumBool, QuantumFloat, QuantumVariable, dicke_state, x, cx, z, control, swap, auto_uncompute, amplitude_amplification
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
                    controls = [q_matrix[k, i + offset - start_column][0] for k in range(i, j)]

                    x(controls)

                    with control(controls):
                        for col in range(i + 1, dim + 1):
                            cx(q_matrix[j, col + offset - start_column], q_matrix[i, col + offset - start_column])

                    x(controls)

                # row reduce
                for j in range(i + 1, dim):
                    with control(q_matrix[j, i + offset - start_column]):
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

        matrix = [
            [1, 0, 1, 1, 1],
            [1, 1, 0, 1, 1],
            [0, 1, 1, 1, 0]
        ]

        good_column_choices = [13, 14, 25, 26, 28, 41, 42, 44, 73, 74, 88, 104]

        return ISDInfo(n, k, good_column_choices, matrix)

    def get_ok_info(self):
        n = 6
        k = 3

        matrix = [
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ]

        good_column_choices = [13, 14, 25, 26, 28, 41, 42, 44]

        return ISDInfo(n, k, good_column_choices, matrix)

    def get_smol_info(self):
        n = 5
        k = 2

        matrix = [
            [1, 1, 1],
            [1, 1, 1],
            [0, 1, 0]
        ]

        good_column_choices = [13, 14, 25, 26]

        return ISDInfo(n, k, good_column_choices, matrix)

    def run_examples(self):
        self.run_superposition_solver(self.get_smol_info())
        print("-" * 50)
        self.run_superposition_solver(self.get_ok_info())
        print("-" * 50)
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
        
        # Calculate theoretical initial probability
        p = len(isd_info.good_column_choices) / math.comb(n, n - k)
        print(f"Expected probability of weight one (before AA): {p:.4f}")

        # Calculate optimal number of iterations for Grover / Amplitude Amplification
        if p > 0:
            iterations = max(1, int(math.pi / 4 / math.sqrt(p)))
        else:
            iterations = 0

        # -------------------------------------------------------------
        # Amplitude Amplification Setup
        # -------------------------------------------------------------
        
        def state_function(B, q_matrix, X):
            # Load the classical matrix using reversible X gates
            for row in range(n - k):
                for col in range(k + 1):
                    if matrix[row][col] == 1:
                        x(q_matrix[row, col])

            x(B[k:])
            dicke_state(B, n - k)
            self.apply_optimisation(B, q_matrix, X, n, k)
            self.controlled_solve(q_matrix, X, n - k, k)

        @auto_uncompute
        def oracle_function(B, q_matrix, X):
            sum_val = QuantumFloat((n - k).bit_length())
            for i in range(n - k):
                with control(q_matrix[i, k]):
                    sum_val += 1
            
            cond = (sum_val == 1)
            z(cond)

        # -------------------------------------------------------------
        
        q_matrix = QuantumArray(qtype=QuantumBool(), shape=(n - k, k + 1))
        X = QuantumArray(qtype=QuantumBool(), shape=(k,))
        B = QuantumVariable(n)

        # 1. Prepare initial state
        state_function(B, q_matrix, X)

        # 2. Apply Amplitude Amplification loop
        if iterations > 0:
            print(f"Applying {iterations} iteration(s) of Amplitude Amplification")
            amplitude_amplification([B, q_matrix, X], state_function, oracle_function, iter=iterations)

        # -------------------------------------------------------------
        # Evaluation
        # -------------------------------------------------------------
        
        # Output 1: Matrix Sum Distribution
        res_matrix = q_matrix.get_measurement()
        print("\nWeight distribution (Sum of last column):")
        weight_distribution = {}

        for matrix_state, prob in res_matrix.items():
            last_col_sum = sum(row[-1] for row in matrix_state)
            
            if last_col_sum in weight_distribution:
                weight_distribution[last_col_sum] += prob
            else:
                weight_distribution[last_col_sum] = prob

        for total, prob in sorted(weight_distribution.items()):
            print(f"Sum: {total:<5} -> {prob * 100:.2f}%") 

        # Output 2: Column Choices (The actual variables that were amplified)
        res_B = B.get_measurement()
        print("\nAmplified Column Choices (Variable B):")
        
        for choice, prob in sorted(res_B.items(), key=lambda item: item[1], reverse=True):
            if prob > 0.001:  # Filter out noise < 0.1%
                # Ensure we have a string representation
                if isinstance(choice, str):
                    bin_str = choice
                else:
                    choice_int = int(choice)
                    bin_str = f"{choice_int:0{n}b}"
                
                # Reverse the string to fix the Endianness mismatch
                reversed_bin_str = bin_str[::-1]
                corrected_decimal = int(reversed_bin_str, 2)
                    
                marker = "<-- TARGET" if corrected_decimal in isd_info.good_column_choices else ""
                print(f"Decimal: {corrected_decimal:<3} | Binary: {reversed_bin_str} -> {prob * 100:.2f}%  {marker}")

if __name__ == "__main__":
    isd = ISD()
    isd.run_examples()