unsafe extern "C" {
    pub type CGame;
    pub type CUnkTask;
}

#[non_exhaustive]
#[repr(C)]
#[derive(Debug)]
pub struct CLevelObject {
    pad0: u32,
    pub id: u16,
}

#[repr(C)]
#[derive(Debug)]
pub struct CLevelNumber {
    pub task_id: u32,
    pub chap_id: u32,
}
