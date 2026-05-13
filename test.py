import qrisp
from qrisp import QuantumArray, QuantumBool
import importlib.metadata

# 1. Get version the "official" way
try:
    version = importlib.metadata.version("qrisp")
    print(f"Qrisp Version (Metadata): {version}")
except Exception:
    print("Could not find version via metadata.")

# 2. Check where the library is actually living
print(f"Library Location: {qrisp.__path__}")

# 3. THE ULTIMATE TEST: Is QuantumArray hashable?
q_arr = QuantumArray(qtype=QuantumBool(), shape=(2, 2))

print("\n--- Hashing Test ---")
try:
    h = hash(q_arr)
    print(f"SUCCESS: QuantumArray is hashable. Hash: {h}")
except TypeError as e:
    print(f"FAILURE: QuantumArray is NOT hashable. Error: {e}")

# 4. Check what AA sees
print("\n--- Internal Dict Test ---")
test_dict = {}
try:
    test_dict[q_arr] = "Works"
    print("SUCCESS: Dictionary assignment works.")
except TypeError:
    print("FAILURE: Dictionary assignment failed (Unhashable).")