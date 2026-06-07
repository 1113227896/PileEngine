from typing import Dict, Any


class PileCalculator:
    """
    单方案深度结构强度核算：D 路线实现。
    """

    def collect_pile_parameters(self) -> Dict[str, Any]:
        """
        交互式收集桩型参数。
        
        逐步引导用户输入桩身材料、截面、标高、桩长、重度、直径及壁厚，
        每步后显示已输入数据并提供修改选项，最后确认所有输入。
        
        返回:
            包含完整桩型参数的字典
        """
        pile_params = {}
        
        # 第 1 步：桩身材料
        while True:
            print("\n" + "="*70)
            print("第 1 步：选择桩身材料")
            print("="*70)
            if pile_params:
                print(f"【已输入数据】{self._format_params(pile_params)}\n")
            
            print("请选择桩身材料:")
            print("  1) UHC：C105")
            print("  2) PHC：C80")
            print("  3) PC：C60")
            
            material_choice = input("请输入选择 (1/2/3) [或输入 'c' 返回上一步]: ").strip()
            
            if material_choice.lower() == 'c':
                if pile_params:
                    print("返回修改")
                    continue
                else:
                    print("无数据可返回")
                    continue
            
            material_map = {
                '1': 'UHC：C105',
                '2': 'PHC：C80',
                '3': 'PC：C60',
            }
            
            if material_choice in material_map:
                pile_params['桩身材料'] = material_map[material_choice]
                break
            else:
                print("无效选择，请输入 1、2、3 或 'c' 返回")
        
        # 第 2 步：桩截面
        while True:
            print("\n" + "="*70)
            print("第 2 步：选择桩截面")
            print("="*70)
            print(f"【已输入数据】{self._format_params(pile_params)}\n")
            
            print("请选择桩截面:")
            print("  1) 圆桩")
            print("  2) 方桩")
            
            section_choice = input("请输入选择 (1/2) [或输入 'c' 返回上一步]: ").strip()
            
            if section_choice.lower() == 'c':
                del pile_params['桩身材料']
                break
            
            section_map = {
                '1': '圆桩',
                '2': '方桩',
            }
            
            if section_choice in section_map:
                pile_params['桩截面'] = section_map[section_choice]
                break
            else:
                print("无效选择，请输入 1、2 或 'c' 返回")
        
        # 第 3 步：桩顶标高
        while True:
            print("\n" + "="*70)
            print("第 3 步：输入桩顶标高（相对标高，单位：m）")
            print("="*70)
            print(f"【已输入数据】{self._format_params(pile_params)}\n")
            
            top_elev_input = input("请输入桩顶标高 [或输入 'c' 返回上一步]: ").strip()
            
            if top_elev_input.lower() == 'c':
                del pile_params['桩截面']
                break
            
            try:
                top_elev = float(top_elev_input)
                pile_params['桩顶标高_m'] = top_elev
                break
            except ValueError:
                print("无效输入，请输入数字或 'c' 返回")
        
        # 第 4 步：桩长
        while True:
            print("\n" + "="*70)
            print("第 4 步：输入桩长（单位：m）")
            print("="*70)
            print(f"【已输入数据】{self._format_params(pile_params)}\n")
            
            length_input = input("请输入桩长 [或输入 'c' 返回上一步]: ").strip()
            
            if length_input.lower() == 'c':
                del pile_params['桩顶标高_m']
                break
            
            try:
                length = float(length_input)
                if length <= 0:
                    print("桩长必须大于 0，请重新输入")
                    continue
                pile_params['桩长_m'] = length
                break
            except ValueError:
                print("无效输入，请输入正数或 'c' 返回")
        
        # 第 5 步：桩身重度
        while True:
            print("\n" + "="*70)
            print("第 5 步：输入桩身重度（单位：kN/m³，默认 25 kN/m³）")
            print("="*70)
            print(f"【已输入数据】{self._format_params(pile_params)}\n")
            
            weight_input = input("请输入桩身重度 [或按 Enter 采用默认值 25，或输入 'c' 返回]: ").strip()
            
            if weight_input.lower() == 'c':
                del pile_params['桩长_m']
                break
            
            if weight_input == '':
                pile_params['桩身重度_kN_m3'] = 25.0
                break
            
            try:
                weight = float(weight_input)
                if weight <= 0:
                    print("桩身重度必须大于 0，请重新输入")
                    continue
                pile_params['桩身重度_kN_m3'] = weight
                break
            except ValueError:
                print("无效输入，请输入正数、按 Enter 使用默认值或输入 'c' 返回")
        
        # 第 6 步：桩身直径及壁厚
        while True:
            print("\n" + "="*70)
            print("第 6 步：输入桩身直径及壁厚")
            print("="*70)
            print(f"【已输入数据】{self._format_params(pile_params)}\n")
            
            if pile_params.get('桩截面') == '圆桩':
                diameter_input = input("请输入桩身直径（单位：m） [或输入 'c' 返回上一步]: ").strip()
                
                if diameter_input.lower() == 'c':
                    del pile_params['桩身重度_kN_m3']
                    break
                
                try:
                    diameter = float(diameter_input)
                    if diameter <= 0:
                        print("直径必须大于 0")
                        continue
                    pile_params['桩身直径_m'] = diameter
                    
                    wall_thick_input = input("请输入壁厚（单位：m，实心圆桩输入 0） [或输入 'c' 返回上一步]: ").strip()
                    
                    if wall_thick_input.lower() == 'c':
                        del pile_params['桩身直径_m']
                        break
                    
                    try:
                        wall_thick = float(wall_thick_input)
                        if wall_thick < 0:
                            print("壁厚不能为负数")
                            del pile_params['桩身直径_m']
                            continue
                        if wall_thick >= diameter:
                            print("壁厚必须小于直径")
                            del pile_params['桩身直径_m']
                            continue
                        pile_params['桩身壁厚_m'] = wall_thick
                        break
                    except ValueError:
                        print("无效输入，请输入数字或 'c' 返回")
                        del pile_params['桩身直径_m']
                except ValueError:
                    print("无效输入，请输入数字或 'c' 返回")
            
            else:  # 方桩
                side_length_input = input("请输入方桩边长（单位：m） [或输入 'c' 返回上一步]: ").strip()
                
                if side_length_input.lower() == 'c':
                    del pile_params['桩身重度_kN_m3']
                    break
                
                try:
                    side_length = float(side_length_input)
                    if side_length <= 0:
                        print("边长必须大于 0")
                        continue
                    pile_params['方桩边长_m'] = side_length
                    
                    wall_thick_input = input("请输入壁厚（单位：m，实心方桩输入 0） [或输入 'c' 返回上一步]: ").strip()
                    
                    if wall_thick_input.lower() == 'c':
                        del pile_params['方桩边长_m']
                        break
                    
                    try:
                        wall_thick = float(wall_thick_input)
                        if wall_thick < 0:
                            print("壁厚不能为负数")
                            del pile_params['方桩边长_m']
                            continue
                        if wall_thick >= side_length:
                            print("壁厚必须小于边长")
                            del pile_params['方桩边长_m']
                            continue
                        pile_params['桩身壁厚_m'] = wall_thick
                        break
                    except ValueError:
                        print("无效输入，请输入数字或 'c' 返回")
                        del pile_params['方桩边长_m']
                except ValueError:
                    print("无效输入，请输入数字或 'c' 返回")
        
        # 最后确认
        print("\n" + "="*70)
        print("【输入确认】")
        print("="*70)
        print(self._format_params(pile_params, verbose=True))
        print("="*70)
        
        while True:
            confirm = input("确认以上输入无误？(y/n): ").strip().lower()
            if confirm == 'y':
                return pile_params
            elif confirm == 'n':
                print("返回重新输入...")
                return self.collect_pile_parameters()
            else:
                print("请输入 'y' 或 'n'")

    def _format_params(self, params: Dict[str, Any], verbose: bool = False) -> str:
        """
        格式化参数显示。
        """
        if not params:
            return "（无数据）"
        
        if verbose:
            lines = []
            for key, value in params.items():
                lines.append(f"  {key}: {value}")
            return "\n".join(lines)
        else:
            items = [f"{k}={v}" for k, v in params.items()]
            return " | ".join(items)

    def run(self, design_loads: Dict[str, Any], soil_layers: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 D 路线的深度结构强度计算。

        支持按桩型选择计算规则，当前支持：
            - 406管桩
            - 405方桩
            - 劲性复合桩
            - 搅拌植桩
        """
        pile_type = str(design_loads.get('pile_type', '406管桩')).strip() or '406管桩'
        pile_length = self._parse_float(design_loads.get('pile_length', 12.0), 'pile_length')
        axial_load = self._parse_float(design_loads.get('axial_load', 0.0), 'axial_load')
        moment = self._parse_float(design_loads.get('moment', 0.0), 'moment')
        shear = self._parse_float(design_loads.get('shear', 0.0), 'shear')

        soil_properties = soil_layers.get('soil_properties', [])
        thickness_by_borehole = soil_layers.get('thickness_by_borehole', {})

        avg_unit_weight = (
            sum(layer.get('土的重度', 0.0) for layer in soil_properties) / len(soil_properties)
            if soil_properties else 0.0
        )
        max_friction_angle = max(
            (layer.get('内摩擦角', 0.0) for layer in soil_properties),
            default=0.0
        )

        total_thickness = 0.0
        if thickness_by_borehole:
            first_borehole = next(iter(thickness_by_borehole.values()))
            total_thickness = sum(layer.get('地层厚度', 0.0) for layer in first_borehole)

        capacities = self._calc_capacity_by_type(
            pile_type,
            pile_length,
            avg_unit_weight,
            max_friction_angle,
            total_thickness,
        )

        axial_capacity = capacities['axial_capacity']
        bending_capacity = capacities['bending_capacity']
        shear_capacity = capacities['shear_capacity']
        uplift_capacity = capacities['uplift_capacity']

        utilization = {
            'axial_utilization': round(abs(axial_load) / axial_capacity, 4) if axial_capacity > 0 else float('inf'),
            'moment_utilization': round(abs(moment) / bending_capacity, 4) if bending_capacity > 0 else float('inf'),
            'shear_utilization': round(abs(shear) / shear_capacity, 4) if shear_capacity > 0 else float('inf'),
            'uplift_utilization': round(max(0.0, -axial_load) / uplift_capacity, 4) if uplift_capacity > 0 else float('inf'),
        }

        max_utilization = max(utilization.values())
        status = '合格' if max_utilization <= 1.0 else '不合格'
        message = '深度结构强度核算通过' if status == '合格' else '深度结构强度核算未通过，请调整桩型或荷载'

        return {
            'route': 'D',
            'route_name': '深度结构强度核算',
            'pile_type': pile_type,
            'status': status,
            'message': message,
            'capacities': {
                'axial_capacity_kN': round(axial_capacity, 2),
                'bending_capacity_kN_m': round(bending_capacity, 2),
                'shear_capacity_kN': round(shear_capacity, 2),
                'uplift_capacity_kN': round(uplift_capacity, 2),
            },
            'utilization': utilization,
            'soil_summary': {
                'avg_unit_weight_kN_m3': round(avg_unit_weight, 3),
                'max_friction_angle_deg': round(max_friction_angle, 3),
                'total_thickness_m': round(total_thickness, 3),
            },
        }

    def _calc_capacity_by_type(
        self,
        pile_type: str,
        pile_length: float,
        avg_unit_weight: float,
        max_friction_angle: float,
        total_thickness: float,
    ) -> Dict[str, float]:
        """
        根据桩型选择对应的计算规则。

        通过映射方式管理多个桩型规则，便于后续扩展。
        """
        def rule_406() -> Dict[str, float]:
            return {
                'axial_capacity': max(220.0, total_thickness * 30.0 + 240.0) * 1.12,
                'bending_capacity': max(200.0, pile_length * 16.0 + avg_unit_weight * 2.5) * 1.25,
                'shear_capacity': max(150.0, avg_unit_weight * 10.0 + max_friction_angle * 2.8 + 80.0),
                'uplift_capacity': max(0.48 * max(220.0, total_thickness * 30.0 + 240.0) * 1.12, 70.0),
            }

        def rule_405() -> Dict[str, float]:
            return {
                'axial_capacity': max(200.0, total_thickness * 28.0 + 220.0) * 1.05,
                'bending_capacity': max(180.0, pile_length * 14.0 + avg_unit_weight * 2.2) * 1.10,
                'shear_capacity': max(140.0, avg_unit_weight * 9.5 + max_friction_angle * 2.5 + 75.0),
                'uplift_capacity': max(0.45 * max(200.0, total_thickness * 28.0 + 220.0) * 1.05, 65.0),
            }

        def rule_composite() -> Dict[str, float]:
            return {
                'axial_capacity': max(240.0, total_thickness * 32.0 + 260.0) * 1.15,
                'bending_capacity': max(220.0, pile_length * 18.0 + avg_unit_weight * 2.8) * 1.30,
                'shear_capacity': max(170.0, avg_unit_weight * 11.0 + max_friction_angle * 3.2 + 90.0),
                'uplift_capacity': max(0.50 * max(240.0, total_thickness * 32.0 + 260.0) * 1.15, 85.0),
            }

        def rule_mixed() -> Dict[str, float]:
            return {
                'axial_capacity': max(210.0, total_thickness * 29.0 + 230.0) * 1.08,
                'bending_capacity': max(190.0, pile_length * 15.0 + avg_unit_weight * 2.4) * 1.18,
                'shear_capacity': max(155.0, avg_unit_weight * 10.2 + max_friction_angle * 2.9 + 82.0),
                'uplift_capacity': max(0.47 * max(210.0, total_thickness * 29.0 + 230.0) * 1.08, 72.0),
            }

        rule_map = {
            '406管桩': rule_406,
            '405方桩': rule_405,
            '劲性复合桩': rule_composite,
            '搅拌植桩': rule_mixed,
        }
        return rule_map.get(pile_type, rule_406)()

    def _parse_float(self, value: Any, field_name: str) -> float:
        if value is None or value == '':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"字段 '{field_name}' 必须为数字: {value}")
git config --global user.name "您的用户名"