## 发布步骤

### 更新版本
1. 修改 __version__.py

### 创建发布包

pip install build

python -m build

pip install dist/dailycheckin-0.1.0-py3-none-any.whl

### 发布
twine upload dist/*