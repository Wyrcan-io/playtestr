from pathlib import Path
Path('hook-result.txt').write_text('hook executed\n',encoding='utf-8',newline='\n')
print('Reviewed local generation hook completed')
