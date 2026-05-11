with open("P5_MATS_Indicator.pine", "r") as f:
    lines = f.readlines()

with open("P5_MATS_Indicator.pine", "w") as f:
    for line in lines:
        if "adx_valid_long  =" in line:
            # We want to keep the condition clean
            f.write("adx_valid_long  = h1_adx > baseAdxThr and (h1_adx >= h1_adx[1] or h1_adx > h1_adx[2]) // Rising or flat\n")
        elif 'string adx_str = str.tostring(h1_adx, "#.#") + (adx_valid_long ? " (Valid)" : " (Weak)")' in line:
            # We will print the threshold in the dashboard so the user can see why it's weak
            f.write('    string adx_str = str.tostring(h1_adx, "#.#") + (adx_valid_long ? " (Valid)" : (" (Weak, < " + str.tostring(baseAdxThr) + " or Falling)"))\n')
        else:
            f.write(line)
