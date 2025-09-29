# ForwardBot 使用说明

## 命令装饰器语法

本项目已更新为使用 `@command_registry.command`、`@option`、`@param` 装饰器语法，支持更灵活的命令参数处理。

## 可用命令

### 1. 查看统计信息

```bash
/stats                    # 查看基本统计信息
/stats -v                 # 查看详细统计信息
/stats --verbose          # 查看详细统计信息（完整形式）
```

### 2. 查看规则列表

```bash
/rules                    # 查看简单格式的规则列表
/rules --format=detailed  # 查看详细格式的规则列表
/rules --format=simple    # 查看简单格式的规则列表（默认）
```

### 3. 规则管理

```bash
/rule-add                 # 添加规则（开发中）
/rule-delete <规则名>      # 删除规则（需要二次确认）
/rule-delete <规则名> -f   # 强制删除规则
/rule-delete <规则名> --force  # 强制删除规则（完整形式）
/rule-enable <规则名>      # 启用规则
/rule-disable <规则名>     # 禁用规则
```

## 装饰器语法特性

- **位置参数**：如 `rule_name: str` 可以直接传递，无需 `--name=` 前缀
- **选项参数**：使用 `@option` 装饰器定义，支持 `-v`、`--verbose` 格式
- **命名参数**：使用 `@param` 装饰器定义，支持 `--format=value` 格式
- **参数顺序无关**：可以使用 `/rule-delete --force myRule` 或 `/rule-delete myRule --force`
- **类型安全**：自动处理布尔值、字符串等类型转换

## 示例

```bash
# 查看详细统计
/stats --verbose

# 查看详细格式的规则列表
/rules --format=detailed

# 强制删除规则
/rule-delete 我的规则 --force
/rule-delete --force 我的规则  # 参数顺序无关

# 启用规则
/rule-enable 示例规则
```
