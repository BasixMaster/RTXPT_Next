// RTSS profile calls using the installed SDK sample's x86 ABI.
// Build x86 and load the installed RTSSHooks.dll, as its official sample does.
#define NOMINMAX
#include <windows.h>
#include <tlhelp32.h>
#include <algorithm>
#include <cctype>
#include <iostream>
#include <string>
#include <vector>
#pragma comment(lib,"Advapi32.lib")
static bool elevated()
{
    HANDLE token=nullptr;if(!OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token))return false;
    TOKEN_ELEVATION value{};DWORD bytes=0;
    const bool result=GetTokenInformation(token,TokenElevation,&value,sizeof(value),&bytes)&&value.TokenIsElevated!=0;
    CloseHandle(token);return result;
}
using EnumProfilesFn=DWORD(*)(LPSTR,DWORD);
using LoadProfileFn=void(*)(LPCSTR);
using GetPropertyFn=BOOL(*)(LPCSTR,LPBYTE,DWORD);
using SetPropertyFn=BOOL(*)(LPCSTR,LPBYTE,DWORD);
using SaveProfileFn=void(*)(LPCSTR);
using DeleteProfileFn=void(*)(LPCSTR);
using UpdateProfilesFn=void(*)();
static std::string lower(std::string text){std::transform(text.begin(),text.end(),text.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});return text;}
static bool running(const std::string& profile)
{
    const auto snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);if(snapshot==INVALID_HANDLE_VALUE)throw 10;
    PROCESSENTRY32 entry{};entry.dwSize=sizeof(entry);BOOL more=Process32First(snapshot,&entry);
    if(!more){CloseHandle(snapshot);throw 10;}
    while(more){if(lower(entry.szExeFile)==lower(profile)){CloseHandle(snapshot);return true;}more=Process32Next(snapshot,&entry);}
    CloseHandle(snapshot);return false;
}
static bool exists(EnumProfilesFn enumerate,const std::string& profile)
{
    DWORD size=65536;
    while(size<=8*1024*1024)
    {
        std::vector<char> buffer(size,0);const auto required=enumerate(buffer.data(),size);
        if(required==0)throw 5;
        if(required>=size){size=std::max(size*2,required+1);continue;}
        const std::string list(buffer.data());size_t start=0;
        while(start<=list.size())
        {
            const auto end=list.find(',',start);auto name=list.substr(start,end==std::string::npos?end:end-start);
            name.erase(0,name.find_first_not_of(" \t\r\n"));const auto last=name.find_last_not_of(" \t\r\n");if(last!=std::string::npos)name.resize(last+1);
            if(lower(name)==lower(profile))return true;
            if(end==std::string::npos)break;start=end+1;
        }
        return false;
    }
    throw 6;
}
static void property(GetPropertyFn get)
{
    DWORD value=0;const bool supported=get("FramerateLimit",reinterpret_cast<LPBYTE>(&value),sizeof(value))!=FALSE;
    std::cout << "{\"supported\":" << (supported?"true":"false") << ",\"value\":";
    if(supported)std::cout<<value;else std::cout<<"null";std::cout<<"}";
}
int main(int argc,char** argv)
{
    if(argc!=4)return 2;
    const std::string install=argv[1],profile=argv[2],action=argv[3];
    if(profile.empty()||profile.find_first_of("/\\:")!=std::string::npos||profile.size()<5||lower(profile.substr(profile.size()-4))!=".exe")return 2;
    const auto dll=LoadLibraryExA((install+"\\RTSSHooks.dll").c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
    if(!dll)return 3;
    const auto enumerate=reinterpret_cast<EnumProfilesFn>(GetProcAddress(dll,"EnumProfiles"));
    const auto load=reinterpret_cast<LoadProfileFn>(GetProcAddress(dll,"LoadProfile"));
    const auto get=reinterpret_cast<GetPropertyFn>(GetProcAddress(dll,"GetProfileProperty"));
    const auto set=reinterpret_cast<SetPropertyFn>(GetProcAddress(dll,"SetProfileProperty"));
    const auto save=reinterpret_cast<SaveProfileFn>(GetProcAddress(dll,"SaveProfile"));
    const auto remove=reinterpret_cast<DeleteProfileFn>(GetProcAddress(dll,"DeleteProfile"));
    const auto update=reinterpret_cast<UpdateProfilesFn>(GetProcAddress(dll,"UpdateProfiles"));
    if(!enumerate||!load||!get||!set||!save||!remove||!update){FreeLibrary(dll);return 4;}
    int code=0;
    try
    {
        const bool found=exists(enumerate,profile);
        if(action=="audit")
        {
            std::cout << "{\"read_only\":true,\"process_elevated\":" << (elevated()?"true":"false") << ",\"application_profile_exists\":" << (found?"true":"false") << ",\"global_property\":";
            load("");property(get);std::cout<<",\"property\":";load(profile.c_str());property(get);std::cout<<"}\n";
        }
        else if(action=="apply")
        {
            if(!elevated())throw 11;if(found)throw 7;if(running(profile))throw 10;load(profile.c_str());DWORD zero=0;
            if(!set("FramerateLimit",reinterpret_cast<LPBYTE>(&zero),sizeof(zero)))throw 8;
            save(profile.c_str());update();std::cout<<"{\"apply_requested\":true}\n";
        }
        else if(action=="delete")
        {
            if(!elevated())throw 11;if(running(profile))throw 10;
            // Private controller must verify the exact created-file hash first.
            if(found){remove(profile.c_str());update();}
            std::cout<<"{\"delete_requested\":true}\n";
        }
        else code=2;
    }
    catch(int failure){code=failure;}
    FreeLibrary(dll);return code;
}
