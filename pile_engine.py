import os
import csv
import json
from typing import List, Dict, Any


class PileEngine:
    """
    桩基调度引擎：负责接收设计荷载与地质层参数，校验并生成基础摘要结果。
    """

    def __init__(self):
        """
        初始化 PileEngine 内部状态。
        """
        self.design_loads: Dict[str, Any] = {}
        self.soil_layers: List[Dict[str, Any]] = []

    def validate_design_loads(self, design_loads: Dict[str, Any]) -> Dict[str, float]:
        """
        校验并规范化设计荷载字典。

        期望字段（键名均为小写下划线风格）：
            - axial_load: 轴心静载 (必需, kN)
            - moment: 弯矩 (可选, kN·m, 缺省为 0.0)
            - shear: 剪力 (可选, kN, 缺省为 0.0)

        参数:
            design_loads: 原始设计荷载字典，允许数字或数字字符串

        返回:
            规范化后的设计荷载字典，数值字段均为 float

        抛出:
            ValueError: 当必需字段缺失或不能转换为数字时

        说明:
            本函数保证除了 axial_load 外，moment 与 shear 可以缺省，
            缺省或空值将被解析为 0.0，便于后续验算流程逐步扩展。
        """
        required = ['axial_load']
        numeric_keys = ['axial_load', 'moment', 'shear']
        out: Dict[str, float] = {}

        for key in required:
            if key not in design_loads or str(design_loads.get(key, '')).strip() == '':
                raise ValueError(f"设计荷载缺少必需字段: {key}")

        for key in numeric_keys:
            val = design_loads.get(key, '')
            if val == '' or val is None:
                out[key] = 0.0
                continue
            try:
                out[key] = float(val)
            except (ValueError, TypeError):
                raise ValueError(f"设计荷载字段 '{key}' 必须为数字: {val}")

        return out

    def validate_soil_layers(self, soil_layers: Any) -> Dict[str, Any]:
        """
        校验并规范化土层数据。分两阶段读取数据：

        第一阶段：读取地层属性表
        必需字段:
            - 地层编号 (str, 唯一文本标识符，如"1"、"2-1"、"3-1")
            - 地层名称 (str)
        可选字段（数值字段缺省为 0.0）:
            - 含水率 (%)
            - 土的密度 (g/cm³)
            - 土的重度 (kN/m³)
            - 孔隙比
            - 土的比重
            - 液限 (%)
            - 塑限 (%)
            - 塑性指数
            - 液性指数
            - 压缩系数 (kPa⁻¹)
            - 黏聚力 (kPa)
            - 内摩擦角 (°)
            - 压缩模量 (MPa)
            - 地基土承载力特征值 (kPa)
            - 预制桩桩侧阻力特征值 (kPa)
            - 预制桩桩段阻力特征值 (kPa)
            - 灌注桩桩侧阻力特征值 (kPa)
            - 灌注桩桩端阻力特征值 (kPa)

        第二阶段：按孔位读取地层厚度
        期望结构：thickness_by_borehole 为字典，键为孔位名称，值为包含以下结构的列表：
            [
                {'地层编号': '...', '地层厚度': value},
                ...
            ]

        参数:
            soil_layers: 包含两部分数据的字典
                {
                    'soil_properties': [...],  # 地层属性表
                    'thickness_by_borehole': {...}  # 按孔位的地层厚度
                }

        返回:
            字典，包含规范化的地层属性和各孔位的厚度数据

        抛出:
            ValueError: 当必要字段缺失或数值转换失败时
        """
        # 定义必需与可选字段
        required_fields = {'地层编号', '地层名称'}
        optional_numeric_fields = {
            '含水率', '土的密度', '土的重度', '孔隙比', '土的比重',
            '液限', '塑限', '塑性指数', '液性指数', '压缩系数',
            '黏聚力', '内摩擦角', '压缩模量', '地基土承载力特征值',
            '预制桩桩侧阻力特征值', '预制桩桩段阻力特征值',
            '灌注桩桩侧阻力特征值', '灌注桩桩端阻力特征值'
        }

        # 第一阶段：校验并规范化地层属性表
        if not isinstance(soil_layers, dict):
            raise ValueError("土层数据必须为字典，包含 'soil_properties' 和 'thickness_by_borehole'")

        soil_properties = soil_layers.get('soil_properties', [])
        thickness_by_borehole = soil_layers.get('thickness_by_borehole', {})

        if not isinstance(soil_properties, list) or len(soil_properties) == 0:
            raise ValueError("soil_properties 必须为非空列表")

        normalized_properties = []
        layer_ids_set = set()  # 提前构建地层编号集合，避免重复遍历

        for idx, layer in enumerate(soil_properties):
            if not isinstance(layer, dict):
                raise ValueError(f"第 {idx+1} 条地层属性格式必须为字典")

            # 检查必需字段
            for required_field in required_fields:
                value = str(layer.get(required_field, '')).strip()
                if value == '':
                    raise ValueError(f"第 {idx+1} 条地层属性缺少必需字段: {required_field}")

            layer_id = str(layer.get('地层编号', '')).strip()
            layer_name = str(layer.get('地层名称', '')).strip()

            # 检查地层编号是否重复
            if layer_id in layer_ids_set:
                raise ValueError(f"地层编号 '{layer_id}' 重复定义")
            layer_ids_set.add(layer_id)

            normalized_layer = {
                '地层编号': layer_id,
                '地层名称': layer_name,
            }

            # 规范化可选数值字段，缺省或空白值统一为 0.0
            for optional_field in optional_numeric_fields:
                raw_value = layer.get(optional_field, '')
                if raw_value == '' or raw_value is None:
                    normalized_layer[optional_field] = 0.0
                    continue
                raw_value_str = str(raw_value).strip()
                if raw_value_str == '':
                    normalized_layer[optional_field] = 0.0
                    continue
                try:
                    normalized_layer[optional_field] = float(raw_value_str)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"第 {idx+1} 条地层属性中字段 '{optional_field}' 的值必须为数字: {raw_value}"
                    )

            normalized_properties.append(normalized_layer)

        # 第二阶段：校验并规范化各孔位的地层厚度数据
        if not isinstance(thickness_by_borehole, dict):
            raise ValueError("thickness_by_borehole 必须为字典")

        normalized_thickness = {}
        for borehole_name, thickness_list in thickness_by_borehole.items():
            if not isinstance(thickness_list, list):
                raise ValueError(f"孔位 {borehole_name} 的厚度数据必须为列表")

            borehole_thicknesses = []
            for thickness_idx, thickness_row in enumerate(thickness_list):
                if not isinstance(thickness_row, dict):
                    raise ValueError(f"孔位 {borehole_name} 第 {thickness_idx+1} 行厚度数据格式必须为字典")

                layer_id = str(thickness_row.get('地层编号', '')).strip()
                if layer_id == '':
                    raise ValueError(f"孔位 {borehole_name} 第 {thickness_idx+1} 行缺少 '地层编号'")

                # 验证该地层编号是否在属性表中存在（使用预先构建的集合）
                if layer_id not in layer_ids_set:
                    raise ValueError(f"孔位 {borehole_name} 中的地层编号 '{layer_id}' 不存在于属性表中")

                thickness_val = thickness_row.get('地层厚度', '')
                if thickness_val == '' or thickness_val is None:
                    raise ValueError(f"孔位 {borehole_name} 中地层编号 {layer_id} 的厚度不能为空")

                try:
                    thickness_float = float(thickness_val)
                except (ValueError, TypeError):
                    raise ValueError(f"孔位 {borehole_name} 中地层编号 {layer_id} 的厚度必须为数字: {thickness_val}")

                borehole_thicknesses.append({
                    '地层编号': layer_id,
                    '地层厚度': thickness_float,
                })

            normalized_thickness[borehole_name] = borehole_thicknesses

        return {
            'soil_properties': normalized_properties,
            'thickness_by_borehole': normalized_thickness,
        }

    def startup(self, design_loads: Dict[str, Any], soil_layers: Dict[str, Any]) -> Dict[str, Any]:
        """
        启动引擎：校验输入、保存状态并返回摘要结果。

        参数:
            design_loads: 设计荷载字典
            soil_layers: 包含地层属性表和孔位厚度的字典
                {
                    'soil_properties': [...],
                    'thickness_by_borehole': {...}
                }

        返回:
            包含输入回显与统计摘要的字典
        """
        validated_loads = self.validate_design_loads(design_loads)
        validated_layers_data = self.validate_soil_layers(soil_layers)
        self.design_loads = validated_loads
        self.soil_layers = validated_layers_data

        # 从规范化后的地层属性表中统计摘要
        soil_properties = validated_layers_data['soil_properties']
        
        # 统计地层总厚度（按第一个孔位计算，若有多个孔位可扩展为平均值）
        thickness_by_borehole = validated_layers_data['thickness_by_borehole']
        total_thickness = 0.0
        if thickness_by_borehole:
            first_borehole = next(iter(thickness_by_borehole.values()))
            total_thickness = sum(layer['地层厚度'] for layer in first_borehole)

        # 统计地层属性中的最大摩擦角和平均重度
        max_friction = max((layer['内摩擦角'] for layer in soil_properties), default=0.0)
        avg_unit_weight = (
            sum(layer['土的重度'] for layer in soil_properties) / len(soil_properties)
        ) if soil_properties else 0.0

        summary = {
            'design_loads': validated_loads,
            'soil_layers_summary': {
                'soil_properties_count': len(soil_properties),
                'borehole_count': len(thickness_by_borehole),
            },
            'summary': {
                'total_thickness_m': total_thickness,
                'max_friction_angle_deg': max_friction,
                'avg_unit_weight_kN_m3': avg_unit_weight,
            }
        }
        return summary

    def execute_route(self, route: str, design_loads: Dict[str, Any], soil_layers: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据流程路由选择执行。
        功能1: 多方案比选，当前尚未实现，输入A选择。
        功能2: 方案深度结构强度核算，委托 `pile_calculator.PileCalculator` 执行，输入B选择。
        """
        selected = str(route).strip().upper()
        if selected == 'A':
            raise NotImplementedError("暂时未开发方案比选功能")
        if selected == 'B':
            try:
                from pile_calculator import PileCalculator
            except ImportError as exc:
                raise ImportError(f"无法加载 D 路线模块 pile_calculator: {exc}")
            calculator = PileCalculator()
            return calculator.run(design_loads, soil_layers)
        raise ValueError("无效路线选择，请使用 'A'（进入方案比选模块）或'B'（进入深度结构核算模块）。")

    @staticmethod
    def load_design_from_json(folder_path: str, filename: str = 'design_input.json') -> Dict[str, Any]:
        """
        从同目录下的 design_input.json 加载设计荷载（可扩展为其他格式）。

        参数:
            folder_path: 目录路径
            filename: 文件名

        返回:
            设计荷载字典

        抛出:
            FileNotFoundError / JSONDecodeError
        """
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"{filename} 不存在于目录: {folder_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_soil_layers_from_csv(folder_path: str, filename: str = 'soil_layers.csv') -> Dict[str, Any]:
        """
        从同目录下的 soil_layers.csv 加载土层属性，同时读取同目录下的 hole*.csv 作为多个孔位的地层厚度。

        soil_layers.csv 要求首行为字段名，推荐字段:
            layer_id,layer_name,unit_weight,cohesion,friction_angle 等

        hole*.csv 要求首行为字段名，推荐字段:
            layer_id,thickness

        参数:
            folder_path: 目录路径
            filename: soil_properties 文件名

        返回:
            包含 soil_properties 和 thickness_by_borehole 的土层字典
        """
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"{filename} 不存在于目录: {folder_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = []
            for row_idx, row in enumerate(reader, start=1):
                normalized_row: Dict[str, Any] = {}
                for k, v in row.items():
                    raw_key = k.strip()
                    raw_val = v.strip() if v is not None else ''
                    if raw_key in {'地层编号', 'layer_id', 'id', '编号'}:
                        normalized_row['地层编号'] = raw_val
                    elif raw_key in {'地层名称', 'layer_name', 'name'}:
                        normalized_row['地层名称'] = raw_val
                    elif raw_key in {'地层厚度', 'thickness'}:
                        normalized_row['地层厚度'] = raw_val
                    elif raw_key in {'土的重度', 'unit_weight', 'unit_weight_kN_m3'}:
                        normalized_row['土的重度'] = raw_val
                    elif raw_key in {'黏聚力', 'cohesion'}:
                        normalized_row['黏聚力'] = raw_val
                    elif raw_key in {'内摩擦角', 'friction_angle'}:
                        normalized_row['内摩擦角'] = raw_val
                    else:
                        normalized_row[raw_key] = raw_val
                if '地层编号' not in normalized_row or str(normalized_row['地层编号']).strip() == '':
                    raise ValueError(f"{filename} 第 {row_idx} 行缺少地层编号字段")
                rows.append(normalized_row)
            if not rows:
                raise ValueError(f"{filename} 文件中未包含任何数据行")

        thickness_by_borehole: Dict[str, Any] = {}
        hole_files = sorted(
            os.path.join(folder_path, fname)
            for fname in os.listdir(folder_path)
            if fname.lower().endswith('.csv') and 'hole' in fname.lower()
        )
        for hole_path in hole_files:
            borehole_name = os.path.splitext(os.path.basename(hole_path))[0]
            with open(hole_path, 'r', encoding='utf-8') as hf:
                reader = csv.DictReader(hf)
                borehole_thicknesses = []
                for row_idx, row in enumerate(reader, start=1):
                    layer_id = ''
                    thickness_val = ''
                    for k, v in row.items():
                        raw_key = k.strip()
                        raw_val = v.strip() if v is not None else ''
                        if raw_key in {'地层编号', 'layer_id', 'id', '编号'}:
                            layer_id = raw_val
                        elif raw_key in {'地层厚度', 'thickness'}:
                            thickness_val = raw_val
                    if layer_id == '':
                        raise ValueError(
                            f"{os.path.basename(hole_path)} 第 {row_idx} 行缺少地层编号字段"
                        )
                    if thickness_val == '' or thickness_val is None:
                        raise ValueError(
                            f"{os.path.basename(hole_path)} 第 {row_idx} 行地层厚度不能为空"
                        )
                    try:
                        thickness_float = float(thickness_val)
                    except (ValueError, TypeError):
                        raise ValueError(
                            f"{os.path.basename(hole_path)} 第 {row_idx} 行地层厚度必须为数字: {thickness_val}"
                        )
                    borehole_thicknesses.append({
                        '地层编号': layer_id,
                        '地层厚度': thickness_float,
                    })
                if not borehole_thicknesses:
                    raise ValueError(f"{os.path.basename(hole_path)} 未包含任何孔位厚度数据")
                thickness_by_borehole[borehole_name] = borehole_thicknesses

        return {
            'soil_properties': rows,
            'thickness_by_borehole': thickness_by_borehole,
        }

    @staticmethod
    def write_output(folder_path: str, output: Dict[str, Any], filename: str = 'output.json') -> None:
        """
        将结果写入指定输出文件（JSON 格式）。

        参数:
            folder_path: 目录路径
            output: 输出字典
            filename: 输出文件名
        """
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


def main():
    """
    脚本入口：在当前脚本目录查找 design_input.json 与 soil_layers.csv，
    先执行基础校验摘要，再允许用户选择执行模块（A: 多方案比选或 B: 深度结构核算）。
    """
    current_folder = os.path.dirname(os.path.abspath(__file__))
    engine = PileEngine()
    try:
        design = engine.load_design_from_json(current_folder, 'design_input.json')
    except Exception as exc:
        print(f"读取设计荷载失败: {exc}")
        return

    try:
        soil_layers = engine.load_soil_layers_from_csv(current_folder, 'soil_layers.csv')
    except Exception as exc:
        print(f"读取土层数据失败: {exc}")
        return

    try:
        result = engine.startup(design, soil_layers)
    except Exception as exc:
        print(f"校验或执行失败: {exc}")
        return

    # 打印基础校验摘要并写入输出
    if isinstance(result, dict) and 'summary' in result:
        print("基础校验成功，摘要：")
        print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    else:
        print("基础校验结果：")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    engine.write_output(current_folder, result, 'output.json')

    # 用户选择执行模块
    print("\n" + "="*60)
    print("请选择执行模块:")
    print("  A: 多方案比选")
    print("  B: 方案深度结构强度核算")
    print("="*60)
    
    while True:
        route_choice = input("请输入选择 (A/B): ").strip().upper()
        if route_choice in ('A', 'B'):
            break
        print("无效选择，请输入 'A' 或 'B'")
    
    try:
        # 如果选择 B 路由，先交互式收集桩型参数
        if route_choice == 'B':
            from pile_calculator import PileCalculator
            calculator = PileCalculator()
            pile_params = calculator.collect_pile_parameters()
            # 将桩型参数合并到设计荷载中
            design.update(pile_params)
        
        route_result = engine.execute_route(route_choice, design, soil_layers)
        print("\n执行结果：")
        print(json.dumps(route_result, ensure_ascii=False, indent=2))
        engine.write_output(current_folder, route_result, f'output_{route_choice.lower()}.json')
    except Exception as exc:
        print(f"模块执行失败: {exc}")
        return


if __name__ == '__main__':
    main()