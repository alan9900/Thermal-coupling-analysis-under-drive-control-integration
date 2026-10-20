"""Read the opened imported assembly; no native/STEP files are overwritten."""
import json,sys,time
from pathlib import Path
import pythoncom,win32com.client,win32gui,win32con,win32process
from PIL import ImageGrab
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/m3_review/output_gear_clearance'
def get0(obj,name):
    value=getattr(obj,name);return value() if callable(value) else value
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    app=win32com.client.GetActiveObject('SldWorks.Application');app.Visible=True;app.UserControl=True
    doc=app.ActiveDoc
    for _ in range(30):
        if doc is not None and get0(doc,'GetTitle')=='Case0_d50_full':break
        time.sleep(1);doc=app.ActiveDoc
    assert doc is not None,'STEP loading has not completed'
    title=get0(doc,'GetTitle');assert title=='Case0_d50_full',title
    components=doc.GetComponents(False);named={c.Name2.rsplit('/',1)[-1].split('.step-')[0]:c for c in components}
    target=['stage2_gear','gear_case_front','gear_case_rear'];boxes={n:list(named[n].GetBox(False,False)) for n in target}
    doc.ClearSelection2(True);manager=doc.InterferenceDetectionManager
    manager.IgnoreHiddenBodies=False;manager.TreatSubAssembliesAsComponents=False;manager.TreatCoincidenceAsInterference=False;manager.IncludeMultibodyPartInterferences=True
    interferences=get0(manager,'GetInterferences');count=get0(manager,'GetInterferenceCount')
    result=dict(status='PASS_IMPORTED_ASSEMBLY_NO_VOLUME_INTERFERENCE' if count==0 else 'BLOCKED_OR_REQUIRES_REVIEW',software='SOLIDWORKS Premium2023 SP0.1',document=title,
        imported_leaf_components=len(components)-1,interference_count=count,ignore_hidden_bodies=False,treat_subassemblies_as_single=False,treat_coincident_faces_as_interference=False,
        include_multibody_part_interferences=True,component_bounding_boxes_m=boxes,geometry_modified=False,model_saved=False,ANSYS='NOT EXECUTED')
    (OUT/'solidworks_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    get0(manager,'Done');assert count==0,result
    # Isolated view intentionally hides surrounding parts only AFTER testing
    # the entire assembly, and is documented in the screenshot caption.
    for name,c in named.items():
        if name=='Case0_d50_full':continue
        c.Visible=1 if name in target else 0
        if name in target:
            v=[.28,.50,.72,.3,.7,.2,.2,0,0] if name=='stage2_gear' else [.83,.63,.32,.3,.7,.2,.2,.8,0]
            c.MaterialPropertyValues=win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,v)
    doc.ShowNamedView2('*Right',4);doc.ViewZoomtofit2();doc.GraphicsRedraw2()
    windows=[];win32gui.EnumWindows(lambda h,p: windows.append(h) if win32gui.IsWindowVisible(h) and 'SOLIDWORKS' in win32gui.GetWindowText(h) and title in win32gui.GetWindowText(h) else None,None)
    h=windows[0];win32gui.ShowWindow(h,win32con.SW_MAXIMIZE)
    try:win32com.client.Dispatch('WScript.Shell').AppActivate(win32process.GetWindowThreadProcessId(h)[1]);win32gui.SetForegroundWindow(h)
    except Exception:pass
    time.sleep(1)
    if win32gui.GetForegroundWindow()==h:ImageGrab.grab(bbox=win32gui.GetWindowRect(h),all_screens=True).save(OUT/'solidworks_isolated_view.png')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
