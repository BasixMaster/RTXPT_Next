from pathlib import Path
import sys,re,json
import latex2mathml.converter
D=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
count=0;out={}
def math(m,display):
    global count
    count+=1
    text=latex2mathml.converter.convert(m[1],display=display).replace('<math ', '<math class="doc-typeset-math" ',1)
    return '<div class="doc-math-scroll">'+text+'</div>' if display=='block' else text
for p in D.glob('*.md'):
    s=p.read_text(encoding='utf-8')
    s=re.sub(r'\\\[([\s\S]*?)\\\]',lambda m:math(m,'block'),s)
    s=re.sub(r'\\\((.*?)\\\)',lambda m:math(m,'inline'),s)
    out[p.stem]=s
(D/'math-markdown.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(math_expressions=count)))
