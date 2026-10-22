"""Package existing native ANSYS contour captures; never run a thermal solve."""
import csv,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
VIEW=Path('E:/ansys_runs/m4_viewer_20261022')
OUT=ROOT/'results/m4/contour_captures'
OUT.mkdir(exist_ok=True)
STUDY=ROOT/'results/m4/studies/D_normal12_rd95_dt1'
rows=list(csv.DictReader((STUDY/'pilot_temperature_history.csv').open()))
manifest=json.loads((VIEW/'cloud_manifest.json').read_text())
names={
'OUTPUT_BEARING_2':('输出轴后轴承','该轴承是输出轴向壳体传热链上的等效区域，同时加载候选轴承损耗。图中温差说明区域并非等温；不能单凭本图把升温全部归于制动盘。轴承内部接触及油膜尚未标定，不据此判断润滑或寿命。'),
'GEAR_CASE_REAR':('减速器后壳体','这是靠近输出端制动器的壳体区域。壳体同时接收内部损耗经连接传来的热量，并与环境发生对流和辐射交换。其峰值滞后于制动盘峰值；具体制动附加影响应使用相同网格的C减A差值，不能由D工况单图拆分。'),
'OIL_INVENTORY':('减速器润滑油等效区','油液以静止导热实体及有限等效界面表示，另接收M1其他传动损耗候选热源。图中分布不代表真实流动、搅拌或喷油温度场。峰值发生在窗口终点，表示本次记录内仍在累积或重分布热量，不能称已获得长期最高油温。'),
'MOTOR_WINDING':('电机绕组等效区','绕组加载工程分配的铜耗，逆变器热量没有加载于此。图示高温主要反映本场景给定的高负载内部发热与有限散热边界。铜块等效导热、绝缘及浸渍接触未标定，69°C不能视为实际绕组或绝缘热点精度。'),
'OUTPUT_SHAFT':('减速器输出轴','输出轴连接盘毂、支承与减速器内部，是固体导热路径中的一个储热区域。峰值出现在窗口终点，短时盘温回落不意味着轴已达到热平衡。温度云图只反映热场，不构成50mm候选轴的强度或传扭校核。'),
'BRAKE_DISC_HAT':('制动盘与盘帽','制动摩擦热加载于两侧摩擦环，盘帽通过实体导热受热，未直接均匀加载摩擦功率。图中摩擦环与盘帽的温差具有明确加载依据。该峰值对应单次制动及当前预热窗口，不是零再生、连续耐久或所有工况最高温度。'),
'PAD_NEAR':('近侧摩擦片','该摩擦片接收候选10%片侧热量中的一半，并通过有限接触导热。局部峰值约400°C，反映固定热分配和有限片厚下的表面陡温升。无移动摩擦接触、闪温或温变材料标定，不能据此认定真实摩擦片温度或制动安全。'),
'CALIPER':('制动卡钳等效体','卡钳通过片背及安装链间接受热，没有把摩擦总热直接加载到卡钳。短窗口中卡钳温升远小于片表面温升，与热容和有限传热时间相容；不能据此认定长时卡钳、制动液或密封温度安全。'),
'CALIPER_REACTION_BRACKET':('卡钳反力支架','支架连接卡钳与壳体，构成盘片安装链通往电驱系统的一条固体传热支路。当前较小温升属于给定接触参数与短时窗口的预测；不能作为支架隔热效果、螺栓预紧或制动反力承载的验证。'),
'DISC_HUB':('制动盘盘毂','盘毂位于制动盘向输出轴传热的串联链中。盘毂温度明显低于摩擦环，可用于观察当前结构与边界下的温度梯度；热流仍须从对应界面结果读取，不能把各串联截面的热量重复相加。'),
'GEAR_CASE_FRONT':('减速器前壳体','前壳体通过内部件、壳体连接及电机转接区域受热，同时向环境散热。与后壳体比较时应注意二者独立峰值时刻不同。当前图不证明壳体实际接触热阻、对流系数或安装散热条件已经标定。'),
'HUB_REMOVABLE_SLEEVE':('盘毂可拆连接套','该连接套位于盘毂与输出轴之间，是需要保留有限接触导度的安装接口。短时较低温升不等于传热被完全阻断。其传扭能力、接触压力及接触热阻仍属研究限制，本图不提供机械连接认证。'),
'INPUT_BEARING_1':('输入轴轴承一','该区域以轴承等效材料和候选质量建立，加载候选轴承损耗，并通过轴及壳体连接散热。峰值与高负载结束附近的热源变化相关，但各来源贡献须通过热量收支分离。等效温度不是滚动体或内圈接触热点。'),
'INPUT_BEARING_2':('输入轴轴承二','与输入轴轴承一属于同一输入轴支承链。两者峰值差异反映当前几何、局部连接和热边界下的模型响应，不足以推定真实轴承载荷不平衡。内部油膜与滚动接触温度未解析。'),
'INPUT_SHAFT':('减速器输入轴','输入轴通过电机连接套、轴承和一级齿轮区域参与传热。峰值晚于部分轴承峰值，表明当前窗口内存在热量扩散与储存过程。未对轴材料温变或实际接触进行温度标定。'),
'INTERMEDIATE_BEARING_1':('中间轴轴承一','中间轴支承区加载候选轴承损耗并连接中间轴与壳体。图中有限空间温差应作为等效热区结果理解，不能替代滚道局部温度、润滑状态或轴向力验证。'),
'INTERMEDIATE_BEARING_2':('中间轴轴承二','该轴承与中间轴另一支承形成并联的散热与储热连接。两支承峰值接近是当前候选配置的计算结果，不代表实际载荷或接触热阻相同。相应轴向力和寿命不在本次热场整理范围。'),
'INTERMEDIATE_SHAFT':('减速器中间轴','中间轴连接两级传动的热区及两个支承，参与内部损耗的再分配。窗口终点达到本次记录最大值，尚不能据此推断连续运行温度平台。该图使用热简化实体，不解析齿面局部接触温度。'),
'MOTOR_CASE':('电机壳体','电机壳体通过定子及连接区域受热，并施加有限液冷边界。较低外壳温度可以与较高绕组温度同时出现，二者之间存在有限热阻。冷却系数与25°C体温为候选条件，不代表实际冷却回路能力。'),
'MOTOR_GEAR_ADAPTER':('电机减速器转接件','转接件构成电机与减速器壳体之间的固体连接热区。当前温升小，不能把它解读为真实总成中的零耦合。温差与净热流须分别记录，尤其不能由单张温度图确定热流方向始终不变。'),
'MOTOR_INPUT_COUPLING':('电机输入传扭连接套','该连接套用于保留电机转子轴与减速器输入端之间的候选机械及热连接。云图反映等效实体和有限接口的热响应，不验证连接套传扭、接触压力或装配公差。'),
'MOTOR_ROTOR_OTHER':('电机转子及其他损耗等效区','该区域接收M1工程场景分配的转子及其他损耗，未把这部分全部解释为永磁体发热。较低等效温升不能用于宣布磁体无退磁风险；磁体几何、损耗和内部换热尚未独立标定。'),
'MOTOR_ROTOR_SHAFT':('电机转子轴','转子轴通过内部连接及传扭接口参与热量传递。图中低温升是当前工程热源分配、有限窗口和等效热阻共同作用的结果；不是实际高速转子轴的标定温度。'),
'MOTOR_STATOR':('电机定子铁心等效区','该区域加载工程分配的铁耗，并与绕组、壳体进行有限导热。绕组与定子的峰值不同步，不能将独立峰值相减当作同一时刻温差。叠片铁心各向异性及绕组接触热阻仍未知。'),
'OUTPUT_BEARING_1':('输出轴前轴承','该区域与输出轴后轴承共同连接输出轴与壳体，加载候选轴承损耗。比较两者峰值可描述当前模型的支承热分布，但不能区分实际滚道局部摩擦热或验证真实润滑条件。'),
'PAD_FAR':('远侧摩擦片','远侧片与近侧片采用对称候选热量分配，因此峰值非常接近；这是模型设定与响应，不是实测对称性证据。约400°C预测仍受固定90/10盘片分配、静止面热流及常热物性限制。'),
'STAGE1_GEAR':('一级齿轮等效热区','M1齿轮损耗候选中的一半施加到一级从动齿轮等效热区。该图反映简化实体的温度扩散，不解析斜齿局部啮合或瞬时接触闪温。斜齿传动实际损耗未重新标定，不能据此声称效率提高。'),
'STAGE2_GEAR':('二级齿轮等效热区','二级从动齿轮接收另一半齿轮损耗候选热源。与一级热区峰值不同可以来自体积、热容及连接边界差异，不能据温度高低反推两级损耗大小，更不能当作齿面接触温度试验。')}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ordered=[r for r in manifest if r['part']=='WHOLE_ASSEMBLY']+[r for r in manifest if r['part']!='WHOLE_ASSEMBLY']
head=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
lines=['---','title: "M4 Case0 整体与各部件温度云图讲解"','date: "2026年10月22日"','---','',
'# 阅读说明','',
'本册收录29幅已完成ANSYS原生温度云图：1幅整体同步温度场、28幅部件云图。图像直接由ANSYS 2024 R1的已有RTH结果导出，保留软件标识、时刻和色标；未合成温度、未重新求解。目的是便于研究者保存截图、逐件阅读和复核。','',
'所有图片来自Case0无新增隔热罩的D场景：首次驱动、高负载保持60 s、80 km/h开始以0.6g制动及随后30 s冷却。整车再生功率上限30 kW；详细热场只计算单侧。初始、环境及冷却液候选温度均为25°C。D的预热是给定热负荷，不代表普通平路恒速行驶。','',
'结果为S3工程假设下的概念预测，M4继续为PARTIAL。真实材料、损耗分配、接触热阻及冷却条件未完成实物标定。时间步与完整接触及冷却敏感性尚未闭合，本册不新增研究或宣布阶段验收通过。','',
'**先看时间，再看色标。** 整体图固定在76.7535 s；每张部件图选择该部件在已保存时刻中的局部最高温度时刻。各图通常采用独立自动色标，红色只表示该图较高温度，不能跨图直接比较颜色。云图最大值不是体积平均温度，也不是安全允许温度。','',
'SMN和SMX分别表示图示节点的最低和最高温度，TIME为求解时间，TEMP为温度。部件页另列热容加权均温，来源是同一时刻的有限元积分；它不是按节点数量简单平均。','',
'**整体图大部分呈蓝色的原因。** 整体色标约25～393°C，上限由摩擦片控制，轴承、壳体等25～69°C区域被压缩到低色阶；不能把蓝色理解成全体均为25°C或不存在传热。整体外观还会遮挡内部件，需结合部件图读取。','',
'**本册峰值的适用范围。** 它们只对应当前首周期及预热窗口、离散输出时刻；不代表连续耐久全局峰值。约400°C片温依赖固定90/10盘片热量分配和无移动摩擦接触等假设，不能作为测量或安全认证。窗口终点达到最大值的部件尚不能声称已达到长期最高温度。','',
f'证据基线提交：`{head}`。原始记录：`results/m4/studies/D_normal12_rd95_dt1/`；完整来源与截图哈希见本册配套清单 `results/m4/contour_captures/capture_manifest.json`。草稿PR #5保持未合并。','']
records=[]
for i,r in enumerate(ordered,1):
    part=r['part'];t=r['time_s']
    if part=='WHOLE_ASSEMBLY':
        label='整体同步温度场'
        rr=[x for x in rows if abs(float(x['time_s'])-t)<1e-7]
        lo=min(float(x['minimum']) for x in rr);hi=max(float(x['maximum']) for x in rr)
        text='整体图把28个有限元热区置于同一时刻，适合核对总成空间关系及同时温度水平。色标上限由当时的摩擦片温度决定，因此较低温的外壳和制动盘大多落在蓝色端；内部高温还可能被外壳遮挡。应结合下列独立部件图判读，不按外观颜色宣布总成没有热耦合。'
        stats=f'时刻 {t:.4f} s；整体节点范围 {lo:.3f}～{hi:.3f}°C。这是同一时刻的空间范围，并非各部件独立峰值拼接。'
    else:
        label,text=names[part.removeprefix('M4_')]
        rr=next(x for x in rows if x['part']==part and abs(float(x['time_s'])-t)<1e-7)
        lo=float(rr['minimum']);hi=float(rr['maximum']);mean=float(rr['capacity_weighted_mean'])
        assert abs(hi-r['max_C'])<1e-8
        stats=f'窗口内记录峰值时刻 {t:.4f} s；节点范围 {lo:.3f}～{hi:.3f}°C；该时刻热容加权均温 {mean:.3f}°C。'
        if abs(t-max(float(x['time_s']) for x in rows))<1e-7:
            text+=' 本图最大值位于记录窗口终点，后续演化未在此窗口中覆盖。'
    source=VIEW/r['image'];target=OUT/f'{i:02d}_{part}.png'
    shutil.copyfile(source,target)
    lines += [f'# 图{i:02d} {label}','',f'![图{i:02d} {label}  S3概念预测  摄氏度](../results/m4/contour_captures/{target.name})'+'{width=15.8cm}','',stats,'',text,'',f'区域标识：`{part}`。软件图中的TIME与本页所列时刻一致；数值保留三位小数仅用于追溯，不代表实物预测精度。','']
    records.append(dict(figure=i,label=label,part=part,time_s=t,minimum_C=lo,maximum_C=hi,
        image=target.name,sha256=sha(target),source_image=str(source),classification='ACTUAL_ANSYS_NATIVE_CAPTURE_S3_NOT_CALIBRATED'))
report=ROOT/'reports/M4_contour_explained.md'
report.write_text('\n'.join(lines),encoding='utf-8')
archive=json.loads((STUDY/'native_archive_manifest.json').read_text())
(OUT/'capture_manifest.json').write_text(json.dumps(dict(status='EXISTING_RESULTS_ONLY',evidence_head=head,
    source_temperature_history_sha256=sha(STUDY/'pilot_temperature_history.csv'),native_result=archive.get('study.rth'),
    figure_count=len(records),figures=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(report,len(records),'native captures; no solve')
