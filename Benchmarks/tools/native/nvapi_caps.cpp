// Cap audit and explicitly requested temporary, exact-path application profiles.
// Default invocation is read-only. Mutations require --apply or --restore.
#include <windows.h>
#include <nvapi.h>
#include <NvApiDriverSettings.h>
#include <iostream>
#include <string>
#include <cstring>
#include <cwchar>
#include <cwctype>
#include <algorithm>

static std::wstring normalizedPath(const wchar_t* path)
{
    std::wstring value(path);
    std::transform(value.begin(),value.end(),value.begin(),[](wchar_t c){return c==L'/'?L'\\':std::towlower(c);});
    return value;
}

static const NvU32 capIds[] = { FRL_FPS_ID, APPIDLE_DYNAMIC_FRL_FPS_ID, VSYNCMODE_ID };
static const NvU32 capValues[] = { 0, 0, VSYNCMODE_FORCEOFF };
static bool copyText(NvAPI_UnicodeString& to, const wchar_t* from)
{
    const auto length=wcslen(from); if(length>=sizeof(to)/sizeof(to[0])) return false;
    std::memcpy(to,from,(length+1)*sizeof(wchar_t)); return true;
}
static int mutate(NvDRSSessionHandle session, const wchar_t* mode,
                  const wchar_t* executable, const wchar_t* profileName)
{
    // Only this tool's UUID-named profiles may be created/restored.
    if (wcsncmp(profileName,L"BasixPT Benchmark ",18)!=0 || wcslen(profileName)!=54
        || !(wcslen(executable)>3 && executable[1]==L':' && (executable[2]==L'\\'||executable[2]==L'/')))
        return 20;
    NvAPI_UnicodeString exe{},name{};
    if(!copyText(exe,executable)||!copyText(name,profileName)) return 20;
    NvDRSProfileHandle existing{},profile{}; NVDRS_APPLICATION app{};app.version=NVDRS_APPLICATION_VER;
    const auto appStatus=NvAPI_DRS_FindApplicationByName(session,exe,&existing,&app);
    const auto found=NvAPI_DRS_FindProfileByName(session,name,&profile);
    if(wcscmp(mode,L"--apply")==0)
    {
        // Refuse every existing application association, even single-app profiles:
        // no user profile, profile metadata or inherited values are rewritten.
        if(appStatus!=NVAPI_EXECUTABLE_NOT_FOUND || found!=NVAPI_PROFILE_NOT_FOUND) return 21;
        NVDRS_PROFILE info{};info.version=NVDRS_PROFILE_VER;copyText(info.profileName,profileName);
        auto status=NvAPI_DRS_CreateProfile(session,&info,&profile);
        if(status!=NVAPI_OK) return 22;
        app={};app.version=NVDRS_APPLICATION_VER;copyText(app.appName,executable);
        status=NvAPI_DRS_CreateApplication(session,profile,&app);
        if(status!=NVAPI_OK) return 23; // unsaved session is discarded by caller
        for(int i=0;i<3;++i)
        {
            NVDRS_SETTING setting{};setting.version=NVDRS_SETTING_VER;
            setting.settingId=capIds[i];setting.settingType=NVDRS_DWORD_TYPE;setting.u32CurrentValue=capValues[i];
            status=NvAPI_DRS_SetSetting(session,profile,&setting);if(status!=NVAPI_OK)return 24;
        }
        if(NvAPI_DRS_SaveSettings(session)!=NVAPI_OK) return 25;
        std::cout << "{\"applied\":true,\"exact_path_profile_created\":true,\"global_mutation\":false}\n";
        return 0;
    }
    if(wcscmp(mode,L"--inspect")==0)
    {
        NVDRS_PROFILE info{};info.version=NVDRS_PROFILE_VER;
        const auto infoStatus=found==NVAPI_OK?NvAPI_DRS_GetProfileInfo(session,profile,&info):found;
        const auto appName=reinterpret_cast<const wchar_t*>(app.appName);
        const auto actual=normalizedPath(appName),expected=normalizedPath(executable);
        const auto base=expected.substr(expected.find_last_of(L'\\')+1);
        std::cout << "{\"read_only\":true,\"lookup_status\":" << appStatus << ",\"profile_status\":" << found
                  << ",\"target_resolves_owned_profile\":" << (existing==profile?"true":"false")
                  << ",\"info_status\":" << infoStatus << ",\"apps\":" << info.numOfApps << ",\"settings\":" << info.numOfSettings
                  << ",\"predefined\":" << info.isPredefined << ",\"app_name_length\":" << actual.size()
                  << ",\"expected_path_length\":" << expected.size() << ",\"slash_normalized_equal\":" << (actual==expected?"true":"false")
                  << ",\"basename_equal\":" << (actual==base?"true":"false")
                  << ",\"folder_length\":" << wcslen(reinterpret_cast<const wchar_t*>(app.fileInFolder))
                  << ",\"launcher_length\":" << wcslen(reinterpret_cast<const wchar_t*>(app.launcher)) << "}\n";
        return 0;
    }
    if(found==NVAPI_PROFILE_NOT_FOUND)
    {
        if(appStatus!=NVAPI_EXECUTABLE_NOT_FOUND) return 26;
        std::cout << "{\"restored\":true,\"already_absent\":true}\n";return 0;
    }
    if(found!=NVAPI_OK || appStatus!=NVAPI_OK || existing!=profile) return 26;
    NVDRS_PROFILE info{};info.version=NVDRS_PROFILE_VER;
    if(NvAPI_DRS_GetProfileInfo(session,profile,&info)!=NVAPI_OK || info.isPredefined || info.numOfApps!=1 || info.numOfSettings!=3) return 27;
    // Refuse cleanup if another actor has changed the task-owned profile.
    // DRS canonicalizes path separators; preserve exact full-path identity while
    // treating Windows '/' and '\\' spellings (and case) as equivalent.
    if(normalizedPath(reinterpret_cast<const wchar_t*>(app.appName))!=normalizedPath(executable)) return 28;
    for(int i=0;i<3;++i)
    {
        NVDRS_SETTING setting{};setting.version=NVDRS_SETTING_VER;
        if(NvAPI_DRS_GetSetting(session,profile,capIds[i],&setting)!=NVAPI_OK
           ||setting.settingLocation!=NVDRS_CURRENT_PROFILE_LOCATION||setting.settingType!=NVDRS_DWORD_TYPE||setting.u32CurrentValue!=capValues[i])return 29;
    }
    if(NvAPI_DRS_DeleteProfile(session,profile)!=NVAPI_OK || NvAPI_DRS_SaveSettings(session)!=NVAPI_OK)return 30;
    std::cout << "{\"restored\":true,\"created_profile_removed\":true,\"global_mutation\":false}\n";return 0;
}

static void setting(NvDRSSessionHandle session, NvDRSProfileHandle profile,
                    const char* name, NvU32 id, bool first)
{
    NVDRS_SETTING value{}; value.version = NVDRS_SETTING_VER;
    const auto status = NvAPI_DRS_GetSetting(session, profile, id, &value);
    std::cout << (first ? "" : ",") << "\"" << name << "\":{\"status\":" << status;
    if (status == NVAPI_OK && value.settingType == NVDRS_DWORD_TYPE)
        std::cout << ",\"value\":" << value.u32CurrentValue
                  << ",\"location\":" << value.settingLocation
                  << ",\"predefined\":" << value.isCurrentPredefined;
    else std::cout << ",\"value\":null";
    std::cout << "}";
}

int wmain(int argc, wchar_t** argv)
{
    if(argc==2&&wcscmp(argv[1],L"--self-test-paths")==0)
    {
        const bool same=normalizedPath(L"C:\\Bench\\Rtxpt.exe")==normalizedPath(L"c:/bench/rtxpt.exe");
        const bool differentFolder=normalizedPath(L"C:\\Other\\Rtxpt.exe")!=normalizedPath(L"C:\\Bench\\Rtxpt.exe");
        const bool basenameInsufficient=normalizedPath(L"Rtxpt.exe")!=normalizedPath(L"C:\\Bench\\Rtxpt.exe");
        std::cout << "{\"same_windows_path_accepted\":" << (same?"true":"false")
                  << ",\"different_folder_rejected\":" << (differentFolder?"true":"false")
                  << ",\"basename_only_rejected\":" << (basenameInsufficient?"true":"false") << "}\n";
        return same&&differentFolder&&basenameInsufficient?0:31;
    }
    const bool mutation=argc==4&&(wcscmp(argv[1],L"--apply")==0||wcscmp(argv[1],L"--restore")==0||wcscmp(argv[1],L"--inspect")==0);
    if (argc != 2 && !mutation) { std::cerr << "Usage: nvapi_caps.exe <exact exe path> | --apply/--restore <exact exe path> <owned profile name>\n"; return 2; }
    const auto init = NvAPI_Initialize();
    if (init != NVAPI_OK) { std::cout << "{\"nvapi_status\":" << init << ",\"coverage\":\"unavailable\"}\n"; return 3; }
    NvDRSSessionHandle session{};
    auto status = NvAPI_DRS_CreateSession(&session);
    if (status != NVAPI_OK) { NvAPI_Unload(); return 4; }
    status = NvAPI_DRS_LoadSettings(session);
    if (status != NVAPI_OK) { NvAPI_DRS_DestroySession(session); NvAPI_Unload(); return 5; }
    if(mutation)
    {
        const auto code=mutate(session,argv[1],argv[2],argv[3]);
        NvAPI_DRS_DestroySession(session);NvAPI_Unload();return code;
    }
    NvAPI_UnicodeString executable{};
    if (wcslen(argv[1]) >= sizeof(executable)/sizeof(executable[0])) return 2;
    std::memcpy(executable, argv[1], wcslen(argv[1])*sizeof(wchar_t));
    NvDRSProfileHandle profile{};
    NVDRS_APPLICATION app{}; app.version = NVDRS_APPLICATION_VER;
    const auto appStatus = NvAPI_DRS_FindApplicationByName(session, executable, &profile, &app);
    const bool applicationProfile = appStatus == NVAPI_OK;
    if (!applicationProfile)
    {
        // Only an absent application is a valid reason to fall back to globals.
        if (appStatus != NVAPI_EXECUTABLE_NOT_FOUND) {
            std::cout << "{\"application_lookup_status\":" << appStatus << ",\"coverage\":\"unknown\"}\n";
            NvAPI_DRS_DestroySession(session); NvAPI_Unload(); return 6;
        }
        status = NvAPI_DRS_GetCurrentGlobalProfile(session, &profile);
        if (status != NVAPI_OK) { NvAPI_DRS_DestroySession(session); NvAPI_Unload(); return 7; }
    }
    std::cout << "{\"schema_version\":1,\"read_only\":true,\"application_profile_found\":"
              << (applicationProfile ? "true" : "false") << ",\"application_lookup_status\":" << appStatus
              << ",\"profile_scope\":\"" << (applicationProfile ? "application_with_inheritance" : "current_global_no_application_entry")
              << "\",\"settings\":{";
    setting(session, profile, "foreground_fps", FRL_FPS_ID, true);
    setting(session, profile, "background_fps", APPIDLE_DYNAMIC_FRL_FPS_ID, false);
    setting(session, profile, "vsync", VSYNCMODE_ID, false);
    std::cout << "},\"external_limiters\":\"unknown; NVAPI does not enumerate third-party limiters\"}\n";
    NvAPI_DRS_DestroySession(session); NvAPI_Unload(); return 0;
}
