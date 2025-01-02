import sys

# 操作碼表 (OPTAB)
OPTAB = {
    "LDA": "00", "STA": "0C", "LDX": "04", "STX": "10",
    "COMP": "28", "JEQ": "30", "JSUB": "48", "J": "3C",
    "CLEAR": "B4", "TIXR": "B8", "RD": "D8", "WD": "DC",
    "TD": "E0", "STCH": "54", "LDCH": "50", "RSUB": "4C",
    "LDT": "74", "STL": "14", "LDB": "68", "JLT": "38",
    "COMPR": "A0"
}

REGISTER_TABLE = {
    "A": 0, "X": 1, "L": 2, "B": 3, "S": 4, "T": 5, "F": 6
}

def assembler(file_path):
    print("=== Step 1: 從檔案讀取輸入 ===")
    try:
        with open(file_path, 'r') as asm_file:
            lines = [line.strip() for line in asm_file if line.strip()]
    except FileNotFoundError:
        print(f"錯誤: 無法找到檔案 {file_path}")
        sys.exit(1)

    print(f"成功讀取檔案: {file_path}")

    # 初始化組譯器
    location_counter = 0
    symbol_table = {}
    text_records = []
    modification_records = []
    current_text = ""
    text_start_address = None
    base_register = None
    program_start = None
    program_name = ""  # 新增變數儲存程式名稱
    header_record = None
    end_record = None
    last_address = 0
    FIXED_TEXT_RECORD_LENGTH = 60

    # 第一階段: 解析輸入代碼，生成符號表
    print("\n=== Step 2: 解析輸入代碼 ===")
    for line in lines:
        parts = line.split()
        if len(parts) == 3:
            label, opcode, operand = parts
        elif len(parts) == 2:
            label, opcode, operand = None, *parts
        else:
            label, opcode, operand = None, parts[0], None

        if opcode == "START":
            program_name = label  # 讀取程式名稱
            program_start = int(operand, 16)
            location_counter = program_start
            print(f"程式名稱: {program_name}, 起始地址: {program_start:06X}")
            continue

        if opcode == "BASE":
            print(f"檢測到 BASE 指令，操作數: {operand}")
            continue

        if label:
            if label in symbol_table:
                print(f"錯誤: 重複的標籤 {label}")
                sys.exit(1)
            symbol_table[label] = location_counter
            print(f"新增標籤 {label}, 地址: {location_counter:04X}")

        if opcode.startswith('+'):
            length = 4
        elif opcode == "BYTE":
            length = len(operand[2:-1]) if operand.startswith("C'") else len(operand[2:-1]) // 2
        elif opcode == "WORD":
            length = 3
        elif opcode == "RESB":
            length = int(operand)
        elif opcode == "RESW":
            length = int(operand) * 3
        elif opcode in OPTAB:
            length = 2 if OPTAB[opcode] in ["A0", "B4", "B8"] else 3
        else:
            length = 3
        last_address = location_counter  # 記錄最後的有效地址
        location_counter += length

    program_length = last_address - program_start
    header_record = f"H^{program_name:<6}^{program_start:06X}^{program_length:06X}"

    print("\n=== Step 3: 生成目標程式碼 ===")
    location_counter = program_start

    for line in lines:
        parts = line.split()
        if len(parts) == 3:
            label, opcode, operand = parts
        elif len(parts) == 2:
            label, opcode, operand = None, *parts
        else:
            label, opcode, operand = None, parts[0], None

        if opcode in ["START", "END", "RESB", "RESW", "BASE"]:
            if opcode == "RESB":
                location_counter += int(operand)  # 增加 RESB 定義的空間大小
            elif opcode == "RESW":
                location_counter += int(operand) * 3  # 增加 RESW 定義的空間大小
            if opcode == "BASE":
                if operand in symbol_table:
                    base_register = symbol_table[operand]
                    print(f"設定 BASE 寄存器為: {base_register:04X}")
                else:
                    print(f"錯誤: BASE 操作數 {operand} 不存在於符號表中")
                    base_register = None
            continue

        if opcode == "BYTE":
            if operand.startswith("C'"):
                code = ''.join(format(ord(c), '02X') for c in operand[2:-1])
            elif operand.startswith("X'"):
                code = operand[2:-1]
            object_code = code
        elif opcode == "WORD":
            value = int(operand)
            object_code = f"{value:06X}"
        elif opcode == "RSUB":
            object_code = "4F0000"
        elif opcode in ["CLEAR", "COMPR", "TIXR"]:
            # Format 2 處理
            op_code = OPTAB[opcode]
            if opcode == "CLEAR":
                r1 = REGISTER_TABLE[operand]
                object_code = f"{op_code}{r1:01X}0"
            elif opcode == "COMPR":
                r1, r2 = operand.split(",")
                object_code = f"{op_code}{REGISTER_TABLE[r1]:01X}{REGISTER_TABLE[r2]:01X}"
            elif opcode == "TIXR":
                r1 = REGISTER_TABLE[operand]
                object_code = f"{op_code}{r1:01X}0"
        else:
            # Format 3/4 處理
            op_code = OPTAB[opcode.lstrip('+')]
            if operand.startswith('#'):
                n_flag, i_flag = 0, 1  # Immediate addressing
                operand = operand[1:]
                if operand.isdigit():
                    address = int(operand)
                else:
                    address = symbol_table.get(operand, 0) - (location_counter + 3)
            elif operand.startswith('@'):
                n_flag, i_flag = 1, 0  # Indirect addressing
                operand = operand[1:]
                address = symbol_table.get(operand, 0) - (location_counter + 3)
            else:
                n_flag, i_flag = 1, 1  # Simple addressing
                address = symbol_table.get(operand, 0) - (location_counter + 3)

            x_flag = 1 if operand and operand.endswith(",X") else 0
            b_flag = 0
            p_flag = 0
            e_flag = 1 if opcode.startswith('+') else 0

            if operand:
                operand = operand.rstrip(',X')

            if e_flag:  # Format 4
                if operand.isdigit():  # 操作數是立即數
                    address = int(operand)  # 直接將常數轉換為地址
                else:  # 操作數是符號
                    address = symbol_table.get(operand, 0)  # 獲取符號地址

                # 組成目標碼
                object_code = (
                    (int(op_code, 16) << 24) |  # 操作碼
                    (n_flag << 25) | (i_flag << 24) |  # 定址模式
                    (x_flag << 23) | (b_flag << 22) | (p_flag << 21) | (e_flag << 20) |  # 標誌位
                    address  # 地址
                )
                object_code = f"{object_code:08X}"  # 格式化為 8 位十六進制

                # 添加修改記錄（適用於符號操作數）
                if not operand.isdigit():  # 如果操作數是符號
                    modification_records.append(f"M^{location_counter + 1:06X}^05")
            else:  # Format 3
                disp = address
                if base_register is not None and (disp > 2047 or disp < -2048):
                    disp = symbol_table.get(operand, 0) - base_register
                    b_flag = 1
                elif operand.isdigit():
                    p_flag = 0
                else:
                    p_flag = 1

                object_code = (int(op_code, 16) << 16) | (n_flag << 17) | (i_flag << 16) | (x_flag << 15) | (b_flag << 14) | (p_flag << 13) | (e_flag << 12) | disp & 0xFFF
                object_code = f"{object_code:06X}"

        if text_start_address is None:
            text_start_address = location_counter
        current_text += object_code
        location_counter += len(object_code) // 2

        # 如果累積的目標碼超過固定長度，輸出並開始新記錄
        while len(current_text) >= FIXED_TEXT_RECORD_LENGTH:
            record_content = current_text[:FIXED_TEXT_RECORD_LENGTH]  # 取前60字符
            current_text = current_text[FIXED_TEXT_RECORD_LENGTH:]   # 剩餘部分保留
            print(f"生成目標程式碼: T^{text_start_address:06X}^1E^{record_content}")
            text_records.append(f"T^{text_start_address:06X}^1E^{record_content}")
            text_start_address += FIXED_TEXT_RECORD_LENGTH // 2  # 每行地址向後移動 30 位元組
    # 處理剩餘的目標碼
    if current_text:
        record_length = len(current_text) // 2  # 剩餘目標碼的實際長度（字節數）
        print(f"生成目標程式碼: T^{text_start_address:06X}^{record_length:02X}^{current_text}")
        text_records.append(f"T^{text_start_address:06X}^{record_length:02X}^{current_text}")


    end_record = f"E^{program_start:06X}"

    print("\n=== Step 4: 輸出符號表 ===")
    print(symbol_table)

    print("\n=== Step 5: 輸出目標程式碼 ===")
    print(header_record)
    for record in text_records:
        print(record)
    for mod in modification_records:
        print(mod)
    print(end_record)

    return symbol_table, text_records, modification_records, header_record, end_record

# 主程式
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python assembler.py <檔案路徑>")
        sys.exit(1)
    file_path = sys.argv[1]
    assembler(file_path)