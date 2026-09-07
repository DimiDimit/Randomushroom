unsafe extern "C" {
    pub type CGame;
}

#[non_exhaustive]
#[repr(C)]
#[derive(Debug)]
pub struct CLevelObject {
    unk0: u32,
    pub id: u16,
}
