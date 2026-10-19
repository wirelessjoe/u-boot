#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0+
"""Host fixture for the actual simplefb probe; requires a C compiler with ASan/UBSan."""
from pathlib import Path
import subprocess,tempfile,sys
source=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[2] / 'drivers/video/simplefb.c').read_text()
function=source.split('static int simple_video_probe',1)[1].split('static const struct udevice_id',1)[0]
prefix=r'''
#include <assert.h>
#undef assert
#define assert(c) do { if (!(c)) { fprintf(stderr, "probe assertion failed\n"); return 1; } } while (0)
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint32_t u32;
typedef uint64_t u64;
typedef uint64_t fdt_addr_t;
typedef uint64_t fdt_size_t;
typedef int ofnode;
#define FDT_ADDR_T_NONE UINT64_MAX
#define VIDEO_BPP16 4
#define VIDEO_BPP32 5
#define VIDEO_X8B8G8R8 0
#define VIDEO_X8R8G8B8 1
#define VIDEO_X2R10G10B10 2
#define VNBYTES(b) ((1U << (b)) / 8)
#define debug(...) ((void)0)
#define log_err(...) ((void)0)
struct udevice { int unused; };
struct video_uc_plat { uint64_t base,size; } plat;
struct video_priv { u32 rot,xsize,ysize,bpix,format,line_length; } priv;
static u32 width=1080,height=2280,stride,rotation;
static bool has_stride,has_rotation;
static uint64_t capacity=0x2400000;
static const char *pixel_format="a8r8g8b8";
static void *dev_get_uclass_plat(struct udevice *d) { return &plat; }
static void *dev_get_uclass_priv(struct udevice *d) { return &priv; }
static ofnode dev_ofnode(struct udevice *d) { return 0; }
static fdt_addr_t dev_read_addr_size(struct udevice *d,fdt_size_t *s) { *s=capacity; return 0x9c400000; }
static void video_set_flush_dcache(struct udevice *d,bool b) {}
static int ofnode_read_u32(ofnode n,const char *key,u32 *value) {
 if (!strcmp(key,"width")) *value=width;
 else if (!strcmp(key,"height")) *value=height;
 else if (!strcmp(key,"stride") && has_stride) *value=stride;
 else if (!strcmp(key,"rot") && has_rotation) *value=rotation;
 else return -EINVAL;
 return 0;
}
static u32 ofnode_read_u32_default(ofnode n,const char *key,u32 fallback) {
 u32 value;return ofnode_read_u32(n,key,&value)?fallback:value;
}
static const char *ofnode_read_string(ofnode n,const char *key) { return pixel_format; }
'''
tests=r'''
int main(void) {
 struct udevice d;
 memset(&priv,0xa5,sizeof(priv));
 assert(simple_video_probe(&d)==0 && priv.rot==0 && priv.line_length==4320);
 has_stride=true; stride=4352;
 assert(simple_video_probe(&d)==0 && priv.line_length==4352);
 has_rotation=true;rotation=1;
 assert(simple_video_probe(&d)==0 && priv.rot==1);
 stride=4319;assert(simple_video_probe(&d)==-EINVAL);
 stride=0;assert(simple_video_probe(&d)==-EINVAL);
 stride=0x100000;assert(simple_video_probe(&d)==-EINVAL);
 stride=4352;capacity=(uint64_t)stride*height-1;
 assert(simple_video_probe(&d)==-EINVAL);
 capacity++;assert(simple_video_probe(&d)==0);
 has_stride=false;pixel_format="r5g6b5";
 assert(simple_video_probe(&d)==0 && priv.line_length==2160);
 width=0;assert(simple_video_probe(&d)==-EINVAL);
 pixel_format="a8r8g8b8"; width=0x80000000U; height=1; capacity=0x100000000ULL;
 assert(simple_video_probe(&d)==-EINVAL);
 puts("ok - real simplefb probe: absent/explicit rotation, packed/padded/16-bit rows, invalid stride and buffer bounds");
}
'''
with tempfile.TemporaryDirectory() as work:
 c=Path(work)/'probe.c';c.write_text(prefix+'static int simple_video_probe'+function+tests)
 binary=Path(work)/'probe'
 subprocess.run(['cc','-O2','-Wall','-Wextra','-Wno-unused-parameter','-fsanitize=address,undefined',str(c),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
