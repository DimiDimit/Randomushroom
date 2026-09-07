pub const ADDRESS_BASE: usize = cfg_select! {
    target_arch = "x86" => 0x00400000,
    target_arch = "x86_64" => 0x140000000,
};

pub const LEVEL_NUMBER_OFFSET: usize = cfg_select! {
    target_arch = "x86" => 0x005A2F10,
    target_arch = "x86_64" => 0x14027CED0,
};

pub const FIND_OBJECT_OFFSET: usize = cfg_select! {
    target_arch = "x86" => 0x00422A70,
    target_arch = "x86_64" => 0x14010DA10,
};
