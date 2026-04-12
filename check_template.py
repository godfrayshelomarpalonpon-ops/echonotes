import sys

f = open(r'C:/Users/Admin/Desktop/echonotes/echonotes/blog/templates/dashboard.html', 'rb')
c = f.read()
f.close()

# Find all occurrences of the curly brace pairs before sug.username
idx = 0
count = 0
while True:
    idx = c.find(b'sug.username', idx)
    if idx == -1:
        break
    print(f"At byte {idx}: {repr(c[idx-5:idx+20])}")
    count += 1
    idx += 1

print(f"Total occurrences: {count}")

# Also check if there's anything unusual with the curly braces
# Find the first {{ near username
idx2 = c.find(b'sug.username')
# Look at the preceding bytes
print("Preceding bytes:", repr(c[idx2-5:idx2]))
