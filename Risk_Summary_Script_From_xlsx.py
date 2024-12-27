import pandas as pd

def summarize_risks_by_subnet(file_path, output_file):
    df = pd.read_excel(file_path)

    if 'Host' not in df.columns or 'Risk' not in df.columns:
        print("File không có cột 'Host' hoặc 'Risk'.")
        return

    df['Subnet'] = df['Host'].apply(lambda x: '.'.join(x.split('.')[:3]))

    summary = df.groupby(['Subnet', 'Risk']).size().unstack(fill_value=0)

    for risk_level in ['Critical', 'High', 'Medium', 'None']:
        if risk_level not in summary.columns:
            summary[risk_level] = 0

    summary = summary.sort_index(key=lambda x: x.map(lambda subnet: list(map(int, subnet.split('.')))))

    result = []
    for subnet, row in summary.iterrows():
        critical = row['Critical']
        high = row['High']
        medium = row['Medium']
        none = row['None']
        result.append(f"{subnet} - {critical} Critical - {high} High - {medium} Medium - {none} None")

    # Ghi kết quả vào file Excel
    summary.reset_index().to_excel(output_file, index=False, columns=['Subnet', 'Critical', 'High', 'Medium', 'None'])

    return result

file_path = "Total.xlsx"
output_file = "Result.xlsx"

results = summarize_risks_by_subnet(file_path, output_file)
if results:
    for line in results:
        print(line)
