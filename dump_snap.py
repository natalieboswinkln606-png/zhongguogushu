import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open('temp/_snap_b_female_full.json', encoding='utf-8') as f:
    snap = json.load(f)

print('=== 基本信息 ===')
print('出生:', snap['input']['datetime'], '性别:', snap['input']['gender'])
print('真太阳时:', snap['true_solar_time'])
print()
print('=== 四柱 ===')
for k, v in snap['pillars'].items():
    print(f'  {k}: {v}')
print()
print('=== 日主 ===')
print('日主:', snap['day_master'])
print()
print('=== 旺弱 ===')
ws = snap['wangshuai']
print(json.dumps(ws, ensure_ascii=False, indent=2))
print()
print('=== 大运 ===')
for step in snap['dayun']['steps']:
    print(f"  {step['index']}. {step['ganzhi']} ({step['start_year']}-{step['end_year']}) god={step['god']}")
print()
print('=== 流年(2020-2040) ===')
for ln in snap['liunian']:
    print(f"  {ln['year']} {ln['ganzhi']} {ln['god']}")

# 保存为另一份可直接读取的中文UTF-8文本
with open('temp/_b_female_dump.txt', 'w', encoding='utf-8') as out:
    out.write('=== 基本信息 ===\n')
    out.write(f"出生: {snap['input']['datetime']} 性别: {snap['input']['gender']}\n")
    out.write(f"真太阳时: {snap['true_solar_time']}\n\n")
    out.write('=== 四柱 ===\n')
    for k, v in snap['pillars'].items():
        out.write(f'  {k}: {v}\n')
    out.write('\n=== 日主 ===\n')
    out.write(f"日主: {snap['day_master']}\n\n")
    out.write('=== 旺弱 ===\n')
    out.write(json.dumps(ws, ensure_ascii=False, indent=2) + '\n\n')
    out.write('=== 十神 ===\n')
    out.write(json.dumps(snap['ten_gods'], ensure_ascii=False, indent=2) + '\n\n')
    out.write('=== 大运 ===\n')
    for step in snap['dayun']['steps']:
        out.write(f"  {step['index']}. {step['ganzhi']} ({step['start_year']}-{step['end_year']}) god={step['god']}\n")
    out.write('\n=== 流年(2020-2040) ===\n')
    for ln in snap['liunian']:
        out.write(f"  {ln['year']} {ln['ganzhi']} {ln['god']}\n")
    out.write('\n=== 紫微(12时辰) ===\n')
    for zw in snap['ziwei_hours']:
        minggong = zw['minggong']
        out.write(f"\n--- 时辰 {zw['hour']} (lunar {zw['lunar']['month']}-{zw['lunar']['day']}) ---\n")
        out.write(f"  命宫: {minggong['zhi']}{minggong['gan']}\n")
        for p in zw['palaces']:
            stars = ','.join(p['stars']) if p['stars'] else ''
            aux = ','.join(p['aux']) if p['aux'] else ''
            sihua = ','.join(p['sihua']) if p['sihua'] else ''
            out.write(f"  {p['name']} {p['zhi']}{p['gan']}: 主星=[{stars}] 辅星=[{aux}] 四化=[{sihua}]\n")
    out.write('\n=== 奇门 ===\n')
    out.write(json.dumps(snap['qimen'], ensure_ascii=False, indent=2) + '\n\n')
    out.write('=== 称骨 ===\n')
    out.write(json.dumps(snap['chenggu'], ensure_ascii=False, indent=2) + '\n\n')
    out.write('=== 元数据(全keys) ===\n')
    out.write(', '.join(snap.keys()) + '\n')
print('\n[OK] dumped to temp/_b_female_dump.txt')
