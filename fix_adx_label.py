import re
with open("P5_MATS_Indicator.pine", "r") as f:
    content = f.read()

# Replace the text " (Weak, < " + str.tostring(baseAdxThr) + " or Falling)" with just " (Weak)"
# but we need to explain to the user why 25.6 is weak.
content = content.replace('(" (Weak, < " + str.tostring(baseAdxThr) + " or Falling)")', '" (Weak)"')

with open("P5_MATS_Indicator.pine", "w") as f:
    f.write(content)
