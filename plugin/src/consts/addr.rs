pub const ADDRESS_BASE: usize = cfg_select! {
    target_arch = "x86" => 0x00400000,
    target_arch = "x86_64" => 0x140000000,
};

// static variables
pub const LEVEL_NUMBER_OFFSET: usize = cfg_select! {
    target_arch = "x86" => 0x005A2F10,
    target_arch = "x86_64" => 0x14027CED0,
};

// modded functions
pub const GATE_CHAPTER_VISUAL_OFFSET: usize = cfg_select! {
    target_arch = "x86" => 0x00411980,
    target_arch = "x86_64" => 0x140022E30,
};

pub const GATE_CHAPTER_ACTUAL_OFFSET: usize = cfg_select! {
    // TODO: find
    target_arch = "x86" => 0x00411980,
    target_arch = "x86_64" => 0x140022E30,
};

// send signals to the rando client
pub const COMPLETE_TASK_OFFSET: usize = cfg_select! {
    target_arch = "x86" => 0x0048FA80,
    target_arch = "x86_64" => 0x1400F4790,
};

pub const FIND_OBJECT_OFFSET: usize = cfg_select! {
    target_arch = "x86" => 0x00422A70,
    target_arch = "x86_64" => 0x14010DA10,
};

// receive signals from the rando client
