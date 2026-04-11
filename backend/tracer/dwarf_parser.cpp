// dwarf_parser.cpp - DWARF Debug Symbol Parser for C++ Binary Tracer
// Week 2: Parse DWARF symbols to get function names and variable info

#ifdef _WIN32
    // Windows: Use DbgHelp API (already implemented in cpp_tracer.cpp)
    #include <windows.h>
    #include <dbghelp.h>
#else
    // Linux/Mac: Use libdwarf or elfutils
    #include <elf.h>
    #include <dwarf.h>
    #include <libdwarf.h>
#endif

#include <string>
#include <vector>
#include <map>
#include <iostream>
#include <fstream>

// C interface for Python ctypes
extern "C" {

// Symbol information structure
struct SymbolInfo {
    char name[256];
    uintptr_t address;
    size_t size;
    int is_function;
    int is_variable;
};

// Variable information with location
struct VariableInfo {
    char name[256];
    char type[128];
    uintptr_t location;  // Memory address or register
    int is_global;
    int is_static;
};

#ifdef _WIN32
// Windows implementation using DbgHelp
__declspec(dllexport) int parse_dwarf_symbols(const char* binary_path, 
                                               SymbolInfo* out_symbols, 
                                               int max_symbols) {
    HANDLE hProcess = GetCurrentProcess();
    
    // Load the module
    DWORD64 baseAddr = SymLoadModuleEx(hProcess, NULL, binary_path, NULL, 0, 0, NULL, 0);
    if (baseAddr == 0) {
        return -1;
    }
    
    // Enumerate symbols
    struct EnumContext {
        SymbolInfo* symbols;
        int max_count;
        int current_count;
    };
    
    EnumContext ctx = { out_symbols, max_symbols, 0 };
    
    auto enumCallback = [](PSYMBOL_INFO pSymInfo, ULONG SymbolSize, PVOID UserContext) -> BOOL {
        EnumContext* ctx = (EnumContext*)UserContext;
        if (ctx->current_count >= ctx->max_count) return FALSE;
        
        SymbolInfo& info = ctx->symbols[ctx->current_count];
        strncpy_s(info.name, pSymInfo->Name, sizeof(info.name) - 1);
        info.address = pSymInfo->Address;
        info.size = pSymInfo->Size;
        info.is_function = (pSymInfo->Tag == SymTagFunction) ? 1 : 0;
        info.is_variable = (pSymInfo->Tag == SymTagData) ? 1 : 0;
        
        ctx->current_count++;
        return TRUE;
    };
    
    SymEnumSymbols(hProcess, baseAddr, NULL, 
                   (PSYM_ENUMERATESYMBOLS_CALLBACK)enumCallback, &ctx);
    
    SymUnloadModule(hProcess, baseAddr);
    
    return ctx.current_count;
}

#else
// Linux implementation using libdwarf
int parse_dwarf_symbols(const char* binary_path, 
                         SymbolInfo* out_symbols, 
                         int max_symbols) {
    Dwarf_Debug dbg;
    Dwarf_Error error;
    int fd;
    
    fd = open(binary_path, O_RDONLY);
    if (fd < 0) {
        return -1;
    }
    
    int res = dwarf_init(fd, DW_DLC_READ, NULL, NULL, &dbg, &error);
    if (res != DW_DLV_OK) {
        close(fd);
        return -1;
    }
    
    // Get compilation units
    Dwarf_Unsigned cu_header_length;
    Dwarf_Half version_stamp;
    Dwarf_Unsigned abbrev_offset;
    Dwarf_Half address_size;
    Dwarf_Unsigned next_cu_header;
    
    int count = 0;
    
    while (count < max_symbols) {
        res = dwarf_next_cu_header(dbg, &cu_header_length, &version_stamp,
                                   &abbrev_offset, &address_size,
                                   &next_cu_header, &error);
        
        if (res == DW_DLV_NO_ENTRY) break;
        if (res != DW_DLV_OK) continue;
        
        // Get DIEs for this CU
        Dwarf_Die cu_die;
        res = dwarf_siblingof(dbg, NULL, &cu_die, &error);
        if (res != DW_DLV_OK) continue;
        
        // Process DIEs recursively
        // (Simplified - full implementation would traverse all DIEs)
        
        dwarf_dealloc(dbg, cu_die, DW_DLA_DIE);
    }
    
    dwarf_finish(dbg, &error);
    close(fd);
    
    return count;
}
#endif

// Get function name from address (cross-platform)
__declspec(dllexport) int get_symbol_at_address(uintptr_t address, 
                                                 char* out_name, 
                                                 int max_len) {
#ifdef _WIN32
    HANDLE hProcess = GetCurrentProcess();
    
    BYTE symbolBuffer[sizeof(SYMBOL_INFO) + 256] = {0};
    SYMBOL_INFO* symbol = (SYMBOL_INFO*)symbolBuffer;
    symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
    symbol->MaxNameLen = 256;
    
    DWORD64 displacement = 0;
    if (SymFromAddr(hProcess, address, &displacement, symbol)) {
        strncpy_s(out_name, max_len, symbol->Name, _TRUNCATE);
        return 1;
    }
#else
    // Linux: Use dladdr or read from /proc/self/maps
    Dl_info info;
    if (dladdr((void*)address, &info) && info.dli_sname) {
        strncpy(out_name, info.dli_sname, max_len - 1);
        out_name[max_len - 1] = '\0';
        return 1;
    }
#endif
    
    return 0;
}

// Unified trace event structure matching Python TraceEvent
struct UnifiedTraceEvent {
    char id[512];
    char event[32];      // "call", "return", "line"
    char function[256];
    char filename[512];
    int lineno;
    char code[512];
    char parent[512];
    char language[32];   // "python", "cpp", "go", "rust"
    
    // Variable tracking (Week 2)
    char reads[10][64];   // Variables read (up to 10)
    int num_reads;
    char writes[10][64];  // Variables written (up to 10)
    int num_writes;
    
    // C++ specific
    uintptr_t address;
    uintptr_t return_address;
};

// Convert DWARF symbols to unified trace format
__declspec(dllexport) int convert_to_trace_events(const char* binary_path,
                                                   UnifiedTraceEvent* out_events,
                                                   int max_events) {
    SymbolInfo symbols[1000];
    int count = parse_dwarf_symbols(binary_path, symbols, 1000);
    
    if (count < 0) return count;
    
    int event_count = 0;
    for (int i = 0; i < count && event_count < max_events; i++) {
        if (symbols[i].is_function) {
            UnifiedTraceEvent& evt = out_events[event_count];
            
            // Build event ID
            snprintf(evt.id, sizeof(evt.id), "%s:%zu:%s", 
                     binary_path, symbols[i].address, symbols[i].name);
            
            strncpy(evt.event, "function", sizeof(evt.event));
            strncpy(evt.function, symbols[i].name, sizeof(evt.function));
            strncpy(evt.filename, binary_path, sizeof(evt.filename));
            evt.lineno = 0;  // Binary doesn't have line numbers directly
            strncpy(evt.code, "", sizeof(evt.code));
            strncpy(evt.parent, "", sizeof(evt.parent));
            strncpy(evt.language, "cpp", sizeof(evt.language));
            
            // No variable info from static analysis
            evt.num_reads = 0;
            evt.num_writes = 0;
            
            evt.address = symbols[i].address;
            evt.return_address = 0;
            
            event_count++;
        }
    }
    
    return event_count;
}

// Test function
__declspec(dllexport) const char* dwarf_version() {
    return "Week 2 DWARF Parser v0.1";
}

} // extern "C"
