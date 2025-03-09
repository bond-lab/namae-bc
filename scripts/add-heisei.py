    for directory, gender in [('boy', 'M'), ('girl', 'F')]:
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                year = int(filename[1:3]) + 1988
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                    names = []
                    for line in file:
                        parts = line.strip().split('\t')
                        if len(parts) == 3:
                            name, frequency = parts[1], int(parts[2])
                            if name == '※希望により削除':
                                deleted[gender] += 1
                            else:
                                names.extend([name] * frequency)
                                data[gender][year] = names
