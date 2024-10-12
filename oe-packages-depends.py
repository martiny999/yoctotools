import re
import subprocess

# 读取 task-depends.dot 文件
try:
    with open('task-depends.dot') as f:
        content = f.read()
        #print("content:\n{}".format(content)) 
    print("成功读取 task-depends.dot 文件。")
except FileNotFoundError:
    print("错误：未找到 task-depends.dot 文件。")
    exit(1)

# 定义依赖字典
package_dependencies = {}

# 黑名单列表
blacklist = ['python', 'glibc', 'aarch64', 'glib-2', 'gcc','systemd','bash','which','sed','perl','gawk']

# 解析任务依赖关系
# 解析任务依赖关系的函数
def parse_package_dependencies(content, package_dependencies, blacklist):
    print("开始解析任务依赖关系...")
    for line in content.splitlines():
        # 匹配依赖关系
        task_match = re.match(r'^\s*"([^"]+)"\s*->\s*"([^"]+)"\s*$', line)
        if task_match:
            src_task = task_match.group(1)
            dest_task = task_match.group(2)

            # 提取 package 名称
            src_package = src_task.split('.')[0]
            dest_package = dest_task.split('.')[0]

            # 检查 src_task 和 dest_task 是否相等
            if src_package == dest_package:
                print(f"跳过相同package: {src_package}")
                continue  # 跳过当前循环

            # 检查是否包含 "native"
            if "native" in src_package or "native" in dest_package:
                print(f"跳过包含 'native' 的 package: {src_package} -> {dest_package}")
                continue  # 跳过当前循环

            # 检查是否包含黑名单中的元素
            if any(blacklist_item in src_package for blacklist_item in blacklist) or \
               any(blacklist_item in dest_package for blacklist_item in blacklist):
                print(f"跳过包含黑名单元素的 package: {src_package} -> {dest_package}")
                continue  # 跳过当前循环

            # 更新依赖字典
            if src_package not in package_dependencies:
                package_dependencies[src_package] = set()
                print(f"发现新 package: {src_package}")

            package_dependencies[src_package].add(dest_package)
            print(f"添加依赖: {src_package} -> {dest_package}")


# 提取包含 label 的行并保存到文件的函数
def extract_labels(content, output_filename):
    print("开始提取包含 label 的行...")
    with open(output_filename, 'w') as label_file:
        for line in content.splitlines():
            # 匹配包含 label 的行
            if 'label=' in line:
                label_match = re.search(r'\[label="([^"]+)"\]', line)
                if label_match:
                    label_content = label_match.group(1)
                    label_file.write(f"{line}\n")  # 将整行写入文件
                    print(f"提取到: {line.strip()}")  # 打印提取的行
                

# 查找依赖链的函数
def find_dependency_chain(package, dependencies, visited=None):
    if visited is None:
        visited = set()
    
    # 如果该 package 已经访问过，直接返回
    if package in visited:
        return []
    
    visited.add(package)
    
    # 创建依赖链
    chain = [package]
    
    # 检查依赖
    if package in dependencies:
        for dep in dependencies[package]:
            chain.extend(find_dependency_chain(dep, dependencies, visited))
    
    return chain

# 生成 DOT 文件的函数
def generate_dot_default(package_chain, filename):
    with open(filename, 'w') as f:
        f.write('digraph G {\n')
        # 写入节点和边
        for package in package_chain:
            f.write(f'    "{package}" [label="{package}"];\n')
            if package in package_dependencies:
                for dep in package_dependencies[package]:
                    f.write(f'    "{package}" -> "{dep}";\n')
        f.write('}\n')


def generate_dot(package_chain, filename):
    added_packages = set()  # 记录已添加的 package
    with open(filename, 'w') as f:
        f.write('digraph G {\n')
        # 写入节点和边
        for package in package_chain:
            if package not in added_packages:
                f.write(f'    "{package}" [label="{package}"];\n')
                added_packages.add(package)
            if package in package_dependencies:
                for dep in package_dependencies[package]:
                    if dep not in added_packages:
                        f.write(f'    "{package}" -> "{dep}";\n')
                        added_packages.add(dep)  # 只添加一次
        f.write('}\n')


# 生成 DOT 文件的函数
def generate_dot_lr(package_chain, filename):
    added_packages = set()  # 记录已添加的 package
    with open(filename, 'w') as f:
        f.write('digraph G {\n')
        f.write('    rankdir=LR;\n')  # 设置从左到右的布局
        # 写入节点和边
        for package in package_chain:
            if package not in added_packages:
                f.write(f'    "{package}" [label="{package}"];\n')
                added_packages.add(package)
            if package in package_dependencies:
                for dep in package_dependencies[package]:
                    if dep not in added_packages:
                        f.write(f'    "{package}" -> "{dep}";\n')
                        added_packages.add(dep)  # 只添加一次
        f.write('}\n')

def generate_png(dot_filename, png_filename):
    try:
        subprocess.run(['dot', '-Tpng', dot_filename, '-o', png_filename], check=True)
        print(f"生成 PNG 文件: {png_filename}")
    except subprocess.CalledProcessError as e:
        print(f"生成 PNG 文件时出错: {e}")
        




# 封装为一个函数
def create_dependency_graph(root_package):
    # 查找依赖链
    dependency_chain = find_dependency_chain(root_package, package_dependencies)
    print(f"{root_package} 的依赖链: {dependency_chain}")

    # 生成 DOT 文件
    dot_filename = root_package+'dependency_chain.dot'
    generate_dot_lr(dependency_chain, dot_filename)
    print(f"生成 DOT 文件: {dot_filename}")

    # 自动执行 dot 命令将 DOT 文件转换为 PNG
    png_filename = root_package+'dependency_chain.png'
    generate_png(dot_filename, png_filename)


# 解析任务依赖关系
parse_package_dependencies(content, package_dependencies, blacklist)
# 提取 labels 并保存到文件
label_filename = 'task_labels.txt'
extract_labels(content, label_filename)
print(f"标签已保存到: {label_filename}")

# 示例：查找某个 package 的依赖链
#root_package = 'vendor-image'
#root_package = 'lib32-skyworth-generic-mediaclient-image'
#root_package = 'lib32-gst-agmplayer'
root_package = 'lib32-curl'

create_dependency_graph(root_package)

#root_package = 'lib32-cobalt-browser'
#create_dependency_graph(root_package)


