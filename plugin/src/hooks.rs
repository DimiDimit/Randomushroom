use std::{cell::RefCell, ffi::c_void, mem, sync::OnceLock};

use fn_abi::abi;
use fn_type_alias::type_alias;
use neohook::{DetourTransaction, Hook};
use winsafe::{self as w, co, prelude::*};

use crate::{
    consts::addr::{ADDRESS_BASE, COMPLETE_TASK_OFFSET, FIND_OBJECT_OFFSET},
    defs::{CGame, CLevelObject},
};

thread_local! {
    pub static ACTIVE_HOOKS: RefCell<Vec<Hook>> = const { RefCell::new(Vec::new()) };
}

static ORIG_COMPLETE_TASK: OnceLock<CompleteTaskFn> = OnceLock::new();
static ORIG_FIND_OBJECT: OnceLock<FindObjectFn> = OnceLock::new();

// #[cfg_attr(target_arch = "x86", abi("thiscall"))]
// #[cfg_attr(target_arch = "x86_64", abi("C"))]
// #[type_alias(GateChapterVisualFn)]
// extern "C" fn gate_chapter_visual_hook() -> bool {
//     true
// }

// #[cfg_attr(target_arch = "x86", abi("thiscall"))]
// #[cfg_attr(target_arch = "x86_64", abi("C"))]
// #[type_alias(GateChapterActualFn)]
// extern "C" fn gate_chapter_actual_hook() -> bool {
//     true
// }

#[cfg_attr(target_arch = "x86", abi("fastcall"))]
#[cfg_attr(target_arch = "x86_64", abi("C"))]
#[type_alias(CompleteTaskFn)]
extern "C" fn complete_task_hook(unk_class: *mut c_void) {
    w::HWND::NULL
        .MessageBox(
            "complete_task_hook before!",
            "Hook",
            co::MB::ICONINFORMATION,
        )
        .unwrap();

    let original = ORIG_COMPLETE_TASK.get().unwrap();
    original(unk_class);

    w::HWND::NULL
        .MessageBox("complete_task_hook after!", "Hook", co::MB::ICONINFORMATION)
        .unwrap();
}

#[cfg_attr(target_arch = "x86", abi("thiscall"))]
#[cfg_attr(target_arch = "x86_64", abi("C"))]
#[type_alias(FindObjectFn)]
extern "C" fn find_object_hook(this: *mut CGame, object: *mut CLevelObject) {
    w::HWND::NULL
        .MessageBox(
            &format!("find_object_hook before! {:#?}", unsafe { &*object }),
            "Hook",
            co::MB::ICONINFORMATION,
        )
        .unwrap();

    let original = ORIG_FIND_OBJECT.get().unwrap();
    original(this, object);

    w::HWND::NULL
        .MessageBox("find_object_hook after!", "Hook", co::MB::ICONINFORMATION)
        .unwrap();
}

pub fn install() {
    let mut session = DetourTransaction::begin();
    session.update_all_threads();

    let main_module_address = w::HINSTANCE::GetModuleHandle(None).unwrap().ptr();
    let main_module_base = unsafe { main_module_address.byte_sub(ADDRESS_BASE) };

    macro hook {
        ($offset:expr, $detour:expr, $sig:ty $(,)?) => {
            {
                let _: $sig = $detour;
                unsafe {
                    mem::transmute::<*mut u8, $sig>(
                        session
                            .attach(main_module_base.byte_add($offset).cast(), $detour as _)
                            .unwrap(),
                    )
                }
            }
        },
        ($offset:expr, $detour:expr, $sig:ty, $orig:expr $(,)?) => {
            let orig_fn = hook!($offset, $detour, $sig);
            $orig.set(orig_fn).unwrap();
        },
    }
    // hook!(
    //     GATE_CHAPTER_VISUAL_OFFSET,
    //     gate_chapter_visual_hook,
    //     GateChapterVisualFn,
    // );
    // i haven't actually found this yet but i wanna leave it here for when i do
    // hook!(
    //     GATE_CHAPTER_ACTUAL_OFFSET,
    //     gate_chapter_visual_hook,
    //     GateChapterActualFn,
    // );
    hook!(
        COMPLETE_TASK_OFFSET,
        complete_task_hook,
        CompleteTaskFn,
        ORIG_COMPLETE_TASK,
    );
    hook!(
        FIND_OBJECT_OFFSET,
        find_object_hook,
        FindObjectFn,
        ORIG_FIND_OBJECT,
    );

    let hooks = session.commit().unwrap();
    ACTIVE_HOOKS.set(hooks);
}

pub fn uninstall() {
    let _ = ACTIVE_HOOKS.try_with(|hooks| {
        let mut hooks = hooks.borrow_mut();
        for hook in hooks.drain(..) {
            hook.unhook().unwrap();
        }
    });
}
