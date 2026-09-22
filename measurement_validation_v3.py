import argparse, cv2, numpy as np
from pathlib import Path
from ultralytics import YOLO

FX=FY=597.5
DEPTH_TO_M=0.001
MAX_DEPTH_M=3.0

def find_label(d,name):
    stem=Path(name).stem
    hits=list(Path(d).glob(stem+'*.txt'))
    if hits:return hits[0]
    key=stem.split('_color')[0]
    hits=list(Path(d).glob(key+'*.txt'))
    if hits:return hits[0]
    raise FileNotFoundError(f'No matching label for {name} in {d}')

def poly_mask(path,w,h):
    m=np.zeros((h,w),np.uint8); n=0
    for line in open(path,encoding='utf-8'):
        p=line.split()
        if not p:continue
        xy=np.asarray([float(x) for x in p[1:]],np.float32).reshape(-1,2)
        xy[:,0]*=w; xy[:,1]*=h
        cv2.fillPoly(m,[np.round(xy).astype(np.int32)],1); n+=1
    if not n:raise ValueError('No polygons in label')
    return m.astype(bool),n

def points3d(depth):
    h,w=depth.shape; u,v=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    z=depth; x=(u-(w-1)/2)*z/FX; y=(v-(h-1)/2)*z/FY
    return np.stack((x,y,z),-1)

def plane_ransac(pts,iters=800,thr=.012):
    if len(pts)<100:raise RuntimeError('Not enough road points')
    rng=np.random.default_rng(42); best=None; bestc=0
    for _ in range(iters):
        a,b,c=pts[rng.choice(len(pts),3,replace=False)]
        n=np.cross(b-a,c-a); norm=np.linalg.norm(n)
        if norm<1e-8:continue
        n/=norm; d=-n.dot(a); dist=np.abs(pts@n+d); count=int((dist<thr).sum())
        if count>bestc:best=(n,d);bestc=count
    if best is None:raise RuntimeError('RANSAC failed')
    n,d=best; dist=np.abs(pts@n+d); q=pts[dist<thr]; cen=q.mean(0); _,_,vh=np.linalg.svd(q-cen,full_matrices=False)
    n=vh[-1]; n/=np.linalg.norm(n); d=-n.dot(cen)
    return n,d,len(q)

def measure(mask,pts,depth,n,d):
    valid=(depth>0)&(depth<=MAX_DEPTH_M)&mask
    if not valid.any():raise RuntimeError('No valid depth pixels in mask')
    cav=np.maximum(np.abs(pts@n+d)[valid],0)
    z=depth[valid]; pixarea=z*z/(FX*FY)
    return dict(valid_pixels=int(valid.sum()),area_m2=float(pixarea.sum()),mean_depth_cm=float(cav.mean()*100),median_depth_cm=float(np.median(cav)*100),p90_depth_cm=float(np.percentile(cav,90)*100),p99_depth_cm=float(np.percentile(cav,99)*100),volume_m3=float((cav*pixarea).sum()))

def diff(pred,gt):return 100*(pred-gt)/gt if abs(gt)>1e-12 else float('nan')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--image',required=True); ap.add_argument('--depth',required=True); ap.add_argument('--label-dir',default='labels/test'); ap.add_argument('--model',required=True); ap.add_argument('--out',default='measurement_validation'); ap.add_argument('--conf',type=float,default=.25); a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    im=cv2.imread(a.image)
    if im is None:raise FileNotFoundError(a.image)
    h,w=im.shape[:2]; raw=np.load(a.depth)
    if raw.shape!=(h,w):raise ValueError(f'Depth {raw.shape} != image {(h,w)}')
    depth=raw.astype(np.float32)*DEPTH_TO_M; valid=(depth>0)&(depth<=MAX_DEPTH_M)
    lp=find_label(a.label_dir,Path(a.image).name);gt,npoly=poly_mask(lp,w,h)
    print(f'Image: {w}x{h}');print(f'Depth: {raw.dtype}, raw range {raw.min()} .. {raw.max()}');print(f'GT label: {lp}');print(f'GT polygons: {npoly}');print(f'Valid depth: {int(valid.sum())}/{h*w} ({100*valid.mean():.2f}%)')
    r=YOLO(a.model).predict(source=a.image,conf=a.conf,imgsz=640,verbose=False)[0]
    if r.masks is None or len(r.boxes)==0:raise RuntimeError('YOLO produced no segmentation detection')
    pmasks=r.masks.data.cpu().numpy(); confs=r.boxes.conf.cpu().numpy(); pred=None;bi=-1;best=-1
    for i,sm in enumerate(pmasks):
        m=cv2.resize(sm,(w,h),interpolation=cv2.INTER_NEAREST)>.5; inter=(m&gt).sum(); union=(m|gt).sum();iou=inter/max(union,1)
        if iou>best:best=float(iou);pred=m;bi=i
    conf=float(confs[bi]); pts=points3d(depth)
    exclude=cv2.dilate((gt|pred).astype(np.uint8),np.ones((15,15),np.uint8),iterations=1).astype(bool)
    rp=pts[valid&~exclude]
    if len(rp)>80000:rp=rp[np.random.default_rng(42).choice(len(rp),80000,replace=False)]
    nn,dd,inliers=plane_ransac(rp);gm=measure(gt,pts,depth,nn,dd);pm=measure(pred,pts,depth,nn,dd)
    print('\n'+'='*68);print('MEASUREMENT VALIDATION: GROUND TRUTH vs YOLO');print('='*68);print(f'YOLO confidence: {conf:.3f}');print(f'Segmentation IoU: {best:.4f}');print(f'Road-plane inliers: {inliers}\n')
    rows=[('Area','area_m2','m2'),('Mean depth','mean_depth_cm','cm'),('Median depth','median_depth_cm','cm'),('P90 depth','p90_depth_cm','cm'),('P99 depth','p99_depth_cm','cm'),('Volume','volume_m3','m3')]
    print(f"{'Metric':<18}{'GROUND TRUTH':>18}{'YOLO MASK':>18}{'DIFF %':>14}");print('-'*68)
    for label,key,_ in rows:print(f'{label:<18}{gm[key]:>18.6f}{pm[key]:>18.6f}{diff(pm[key],gm[key]):>13.2f}%')
    print('-'*68);print(f"{'GT valid pixels':<18}{gm['valid_pixels']:>18}");print(f"{'YOLO valid pixels':<18}{pm['valid_pixels']:>18}\n")
    vis=im.copy();gto=gt&~pred;pro=pred&~gt;ov=gt&pred
    vis[gto]=cv2.addWeighted(vis[gto],.45,np.full_like(vis[gto],(0,0,255)),.55,0);vis[pro]=cv2.addWeighted(vis[pro],.45,np.full_like(vis[pro],(0,255,0)),.55,0);vis[ov]=cv2.addWeighted(vis[ov],.35,np.full_like(vis[ov],(0,255,255)),.65,0)
    c1,_=cv2.findContours(gt.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);c2,_=cv2.findContours(pred.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(vis,c1,-1,(0,0,255),2);cv2.drawContours(vis,c2,-1,(0,255,0),2)
    texts=[f'Seg IoU: {best:.3f}',f'GT area: {gm["area_m2"]:.4f} m2',f'YOLO area: {pm["area_m2"]:.4f} m2',f'GT volume: {gm["volume_m3"]:.6f} m3',f'YOLO volume: {pm["volume_m3"]:.6f} m3',f'Volume diff: {diff(pm["volume_m3"],gm["volume_m3"]):+.2f}%']
    for j,t in enumerate(texts):
        y=25+j*25;cv2.putText(vis,t,(8,y),cv2.FONT_HERSHEY_SIMPLEX,.52,(255,255,255),3);cv2.putText(vis,t,(8,y),cv2.FONT_HERSHEY_SIMPLEX,.52,(0,0,0),1)
    cv2.imwrite(str(out/'gt_vs_yolo_measurement.jpg'),vis)
    cavity=np.clip(np.abs(pts@nn+dd)*100,0,15);norm=np.zeros_like(cavity,dtype=np.uint8);norm[valid]=(cavity[valid]/15*255).astype(np.uint8);dc=cv2.applyColorMap(norm,cv2.COLORMAP_JET);dc[~(gt|pred)]=im[~(gt|pred)]//3;cv2.imwrite(str(out/'cavity_depth_visual.jpg'),dc)
    with open(out/'measurement_validation.csv','w',newline='',encoding='utf-8') as f:
        import csv;wri=csv.writer(f);wri.writerow(['image','yolo_confidence','seg_iou','road_plane_inliers','gt_area_m2','yolo_area_m2','area_diff_pct','gt_mean_depth_cm','yolo_mean_depth_cm','mean_depth_diff_pct','gt_median_depth_cm','yolo_median_depth_cm','median_depth_diff_pct','gt_p90_depth_cm','yolo_p90_depth_cm','p90_depth_diff_pct','gt_p99_depth_cm','yolo_p99_depth_cm','p99_depth_diff_pct','gt_volume_m3','yolo_volume_m3','volume_diff_pct','gt_valid_pixels','yolo_valid_pixels']);wri.writerow([Path(a.image).name,conf,best,inliers,gm['area_m2'],pm['area_m2'],diff(pm['area_m2'],gm['area_m2']),gm['mean_depth_cm'],pm['mean_depth_cm'],diff(pm['mean_depth_cm'],gm['mean_depth_cm']),gm['median_depth_cm'],pm['median_depth_cm'],diff(pm['median_depth_cm'],gm['median_depth_cm']),gm['p90_depth_cm'],pm['p90_depth_cm'],diff(pm['p90_depth_cm'],gm['p90_depth_cm']),gm['p99_depth_cm'],pm['p99_depth_cm'],diff(pm['p99_depth_cm'],gm['p99_depth_cm']),gm['volume_m3'],pm['volume_m3'],diff(pm['volume_m3'],gm['volume_m3']),gm['valid_pixels'],pm['valid_pixels']])
    print(f'Overlay: {out/"gt_vs_yolo_measurement.jpg"}');print(f'Depth:   {out/"cavity_depth_visual.jpg"}');print(f'CSV:     {out/"measurement_validation.csv"}');print('='*68)

if __name__=='__main__':main()
