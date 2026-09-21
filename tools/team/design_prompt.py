"""Design input shared by the resource modal and project documents."""
import tech_stack

PATH = 'docs/product/DESIGN_PROMPT.md'
DEFAULT = """# 디자인 프롬프트

## 만들고 싶은 화면과 사용자

## 원하는 분위기·스타일

## 색상·폰트·레이아웃

## 참고 디자인·Figma 링크

## 꼭 포함할 요소

## 피하고 싶은 요소
"""


def read():
    return tech_stack.read(PATH, DEFAULT)


def save(body):
    return tech_stack.save(body, PATH)
