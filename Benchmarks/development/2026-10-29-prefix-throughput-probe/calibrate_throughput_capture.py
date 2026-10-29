"""Temporary known-value GPU producer; always restore physical shader source/copy."""
from pathlib import Path
import subprocess,sys,json,hashlib
import numpy as np
r=Path(__file__).resolve().parents[1];repo=r/'outputs/RTXDI_Next';tools=repo/'Benchmarks/tools';sys.path.insert(0,str(tools));from analyze_throughput import read,summarize
base=r/'work/2026-10-29-throughput-clamp';producer=repo/'Rtxpt/Shaders/PathTracerSurfaceBridgeDonut.hlsli';original=producer.read_bytes();needle=b'? max(path.GetThp(), 0.0f) : saturate(path.GetThp());';assert needle in original
cmake=r/'work/cmake-toolchain/cmake/data/bin/cmake.exe'
def copy_sources():subprocess.run([str(cmake),'--build',str(r/'work/build-B1'),'--config','Release','--target','ShaderDynamicAssets_CopyAlways','--parallel','1'],check=True,stdout=subprocess.DEVNULL)
def capture(label,strict=False):
 out=base/'calibration'/label;args=[sys.executable,str(tools/'run_capture.py'),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(out),'--label','SYNTHETIC-PREFIX-'+label,'--scene','convergence-test.scene.json','--mode','di','--exposure','0','--width','1280','--height','720','--max-bounces','14','--max-diffuse-bounces','2','--simple','--app-uncapped','--linear-hdr','--nee-mis','0','--environment-diffuse-mip','0','--rounded-gbuffer-materials','0','--preserve-gbuffer-throughput','1','--capture-gbuffer-throughput','--sampling-seed','0','--history-frames','1','--di-mode','3','--strict-di-validation','--timeout','180']
 if strict:args+=['--artifact-manifest',str(base/'calibration-artifacts.json')]
 subprocess.run(args,check=True);weights=read(next(out.glob('*.throughput.bin')));positive=np.any(weights>0,axis=-1);assert positive.any();assert np.all(weights[positive]==np.array([2,.5,4],dtype=np.float32));return summarize(weights)
try:
 producer.write_bytes(original.replace(needle,b'? float3(2.0f, 0.5f, 4.0f) : saturate(path.GetThp());',1));copy_sources()
 (base/'calibration-source.patch').write_bytes(subprocess.check_output(['git','-C',str(repo),'diff','--binary','HEAD','--','Rtxpt','CMakeLists.txt']))
 capture('warm')
 subprocess.run([sys.executable,str(tools/'artifact_manifest.py'),'--repo',str(repo),'--exe',str(repo/'bin/Rtxpt.exe'),'--output',str(base/'calibration-artifacts.json')],check=True)
 stats=capture('verified',True)
 (base/'calibration-result.json').write_text(json.dumps(dict(scope='Synthetic GPU positive control, not a physical renderer/quality sample',expected_positive_rgb=[2,.5,4],statistics=stats,physical_producer_sha256=hashlib.sha256(original).hexdigest()),indent=2)+'\n',encoding='utf-8')
 print('Synthetic positive control passed exact GPU prefix [2,0.5,4]',flush=True)
finally:
 producer.write_bytes(original);copy_sources();assert producer.read_bytes()==original
 (base/'physical-producer-restoration.json').write_text(json.dumps(dict(restored=True,sha256=hashlib.sha256(original).hexdigest(),runtime_source_copy_restored=True),indent=2)+'\n',encoding='utf-8')
 print('Physical producer restored byte-for-byte and copied to runtime',flush=True)
