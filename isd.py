from qrisp import QuantumArray, QuantumBool, x, cx, control

def print_matrix(matrix, title):
    print(f"{title}:")
    for row in matrix:
        r = [int(val) for val in row]
        print(f"{r[0]} {r[1]} {r[2]} | {r[3]}")
    print()

q_matrix = QuantumArray(qtype=QuantumBool(), shape=(3, 4))

classical_matrix = [
    [0, 1, 1, 1],
    [1, 0, 1, 0],
    [1, 1, 1, 1]
]

q_matrix[:] = classical_matrix

print("======================= ISD ======================")
print("Solving the following system of binary equations:")
print("x2 + x3 = 1")
print("x1 + x3 = 0")
print("x1 + x2 + x3 = 1\n")
print("Expected values: x1 = 0, x2 = 1, x3 = 0\n")

print_matrix(classical_matrix, "Input matrix")

n = 3

for i in range(n):
    for j in range(i + 1, n):
        controls = q_matrix[i, i:j]

        x(controls)

        with control([qb[0] for qb in controls]):
            for col in range(i + 1, n + 1):
                cx(q_matrix[j, col], q_matrix[i, col])

        x(controls)

    for j in range(i + 1, n):
        with control(q_matrix[j, i]):
            for col in range(i + 1, n + 1):
                cx(q_matrix[i, col], q_matrix[j, col])

for i in range(n - 1, 0, -1):
    for j in range(i - 1, -1, -1):
        with control(q_matrix[j, i]):
            cx(q_matrix[i, 3], q_matrix[j, 3])

res = q_matrix.get_measurement()
final_state = max(res, key=res.get)
print_matrix(final_state, "Output matrix")

x1 = int(final_state[0][3])
x2 = int(final_state[1][3])
x3 = int(final_state[2][3])
print(f"Calculated values: x1 = {x1}, x2 = {x2}, x3 = {x3}\n")