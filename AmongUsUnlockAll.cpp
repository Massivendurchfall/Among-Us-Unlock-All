#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <urlmon.h>
#include <shlobj.h>
#include <exdisp.h>
#include <comdef.h>
#include <commctrl.h>       // für EM_SETCUEBANNER
#include <string>

#pragma comment(lib, "urlmon.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "comctl32.lib")

#ifndef FOF_NO_UI
#define FOF_NO_UI          0x0400
#endif
#ifndef FOF_NOCONFIRMATION
#define FOF_NOCONFIRMATION 0x0010
#endif
#ifndef FOF_NOCONFIRMMKDIR
#define FOF_NOCONFIRMMKDIR 0x0200
#endif

enum {
    IDC_RADIO_STORE = 101,
    IDC_RADIO_STEAM = 102,
    IDC_EDIT_PATH = 103,
    IDC_BTN_INSTALL = 104,
    IDC_LABEL_CREDIT = 105
};

bool DownloadFile(const std::string& url, const std::string& out) {
    return URLDownloadToFileA(NULL, url.c_str(), out.c_str(), 0, NULL) == S_OK;
}

HRESULT ExtractZipWithShell(const std::wstring& zipPath, const std::wstring& destFolder) {
    HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    if (FAILED(hr)) return hr;
    IShellDispatch* pShell = nullptr;
    hr = CoCreateInstance(CLSID_Shell, NULL, CLSCTX_INPROC_SERVER,
        IID_IShellDispatch, (void**)&pShell);
    if (FAILED(hr)) { CoUninitialize(); return hr; }
    VARIANT vFrom{}, vTo{};
    vFrom.vt = VT_BSTR; vFrom.bstrVal = SysAllocString(zipPath.c_str());
    vTo.vt = VT_BSTR; vTo.bstrVal = SysAllocString(destFolder.c_str());
    Folder* pFrom = nullptr, * pTo = nullptr;
    hr = pShell->NameSpace(vFrom, &pFrom);
    if (SUCCEEDED(hr)) hr = pShell->NameSpace(vTo, &pTo);
    if (SUCCEEDED(hr) && pFrom && pTo) {
        FolderItems* items = nullptr;
        hr = pFrom->Items(&items);
        if (SUCCEEDED(hr) && items) {
            VARIANT vItems{}, vOpts{};
            vItems.vt = VT_DISPATCH;
            vItems.pdispVal = items;
            vOpts.vt = VT_I4;
            vOpts.lVal = FOF_NO_UI | FOF_NOCONFIRMATION | FOF_NOCONFIRMMKDIR;
            hr = pTo->CopyHere(vItems, vOpts);
            VariantClear(&vItems);
            VariantClear(&vOpts);
            items->Release();
        }
    }
    if (pFrom) pFrom->Release();
    if (pTo)   pTo->Release();
    VariantClear(&vFrom);
    VariantClear(&vTo);
    pShell->Release();
    CoUninitialize();
    return hr;
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM w, LPARAM l) {
    static HWND  hEdit, hBtn, hLabel;
    static HBRUSH hbrBg;
    switch (msg) {
    case WM_CREATE: {
        hbrBg = CreateSolidBrush(RGB(32, 32, 32));
        CreateWindowEx(0, WC_BUTTON, L"Select Platform:",
            WS_CHILD | WS_VISIBLE | BS_GROUPBOX,
            10, 10, 360, 90, hwnd, NULL, NULL, NULL);
        CreateWindowEx(0, WC_BUTTON, L"Microsoft Store",
            WS_CHILD | WS_VISIBLE | BS_AUTORADIOBUTTON | WS_GROUP,
            20, 40, 200, 20, hwnd, (HMENU)IDC_RADIO_STORE, NULL, NULL);
        CreateWindowEx(0, WC_BUTTON, L"Steam / Epic / Itch.io",
            WS_CHILD | WS_VISIBLE | BS_AUTORADIOBUTTON,
            20, 65, 200, 20, hwnd, (HMENU)IDC_RADIO_STEAM, NULL, NULL);

        CreateWindowEx(0, WC_STATIC, L"Enter Microsoft Store path manually:",
            WS_CHILD | WS_VISIBLE,
            20, 90, 360, 15, hwnd, NULL, NULL, NULL);

        hEdit = CreateWindowEx(WS_EX_CLIENTEDGE, L"EDIT", L"",
            WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
            20, 110, 350, 22, hwnd, (HMENU)IDC_EDIT_PATH, NULL, NULL);
        EnableWindow(hEdit, FALSE);

        // Placeholder/Cue Banner einrichten
        SendMessageW(hEdit, EM_SETCUEBANNER, (WPARAM)TRUE,
            (LPARAM)L"e.g. C:\\Program Files\\WindowsApps\\InnerSloth.AmongUs_...");

        hBtn = CreateWindowEx(0, WC_BUTTON, L"Install",
            WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            20, 150, 120, 30, hwnd, (HMENU)IDC_BTN_INSTALL, NULL, NULL);

        hLabel = CreateWindowEx(0, WC_STATIC, L"Made by Tapetenputzer",
            WS_CHILD | WS_VISIBLE, 0, 0, 1, 1, hwnd, (HMENU)IDC_LABEL_CREDIT, NULL, NULL);
        HFONT f = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
        SendMessage(hLabel, WM_SETFONT, (WPARAM)f, TRUE);
        RECT rc; GetClientRect(hwnd, &rc);
        const wchar_t* txt = L"Made by Tapetenputzer";
        HDC hdc = GetDC(hwnd);
        HFONT old = (HFONT)SelectObject(hdc, f);
        SIZE sz; GetTextExtentPoint32(hdc, txt, lstrlen(txt), &sz);
        SelectObject(hdc, old); ReleaseDC(hwnd, hdc);
        MoveWindow(hLabel,
            rc.right - sz.cx - 10,
            rc.bottom - sz.cy - 10,
            sz.cx, sz.cy, TRUE);
        break;
    }
    case WM_SIZE: {
        RECT rc; GetClientRect(hwnd, &rc);
        const wchar_t* txt = L"Made by Tapetenputzer";
        HFONT f = (HFONT)SendMessage(hLabel, WM_GETFONT, 0, 0);
        HDC hdc = GetDC(hwnd);
        HFONT old = (HFONT)SelectObject(hdc, f);
        SIZE sz; GetTextExtentPoint32(hdc, txt, lstrlen(txt), &sz);
        SelectObject(hdc, old); ReleaseDC(hwnd, hdc);
        MoveWindow(hLabel,
            rc.right - sz.cx - 10,
            rc.bottom - sz.cy - 10,
            sz.cx, sz.cy, TRUE);
        break;
    }
    case WM_COMMAND:
        switch (LOWORD(w)) {
        case IDC_RADIO_STORE:
        case IDC_RADIO_STEAM:
            EnableWindow(hEdit, LOWORD(w) == IDC_RADIO_STORE);
            break;
        case IDC_BTN_INSTALL: {
            EnableWindow(hBtn, FALSE);
            bool useStore = SendDlgItemMessage(hwnd, IDC_RADIO_STORE,
                BM_GETCHECK, 0, 0) == BST_CHECKED;
            std::string url; std::wstring dest;
            if (useStore) {
                url = "https://github.com/astra1dev/AUnlocker/releases/download/v1.1.8/"
                    "AUnlocker_v1.1.8_MicrosoftStore.zip";
                int len = GetWindowTextLengthW(hEdit) + 1;
                std::wstring tmp(len, L'\0');
                GetWindowTextW(hEdit, &tmp[0], len);
                dest = tmp;
            }
            else {
                url = "https://github.com/astra1dev/AUnlocker/releases/download/v1.1.8/"
                    "AUnlocker_v1.1.8_Steam_Epic_Itch.zip";
                dest = L"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Among Us";
            }
            DWORD a = GetFileAttributesW(dest.c_str());
            if (a == INVALID_FILE_ATTRIBUTES || !(a & FILE_ATTRIBUTE_DIRECTORY)) {
                std::wstring msg = L"Zielordner existiert nicht:\n" + dest;
                MessageBoxW(hwnd, msg.c_str(), L"Error", MB_ICONERROR);
                EnableWindow(hBtn, TRUE); break;
            }
            CHAR tp[MAX_PATH];
            if (!GetTempPathA(MAX_PATH, tp)) {
                MessageBoxW(hwnd, L"Temp folder error!", L"Error", MB_ICONERROR);
                EnableWindow(hBtn, TRUE); break;
            }
            std::string tmpZip = std::string(tp) + "amod.zip";
            if (!DownloadFile(url, tmpZip)) {
                MessageBoxW(hwnd, L"Download failed!", L"Error", MB_ICONERROR);
                EnableWindow(hBtn, TRUE); break;
            }
            HRESULT hr = ExtractZipWithShell(
                std::wstring(tmpZip.begin(), tmpZip.end()), dest);
            if (FAILED(hr)) {
                MessageBoxA(hwnd, "Extraction failed!", "Error", MB_ICONERROR);
                EnableWindow(hBtn, TRUE); break;
            }
            DeleteFileA(tmpZip.c_str());
            MessageBoxW(hwnd, L"Installation successful!", L"Done", MB_ICONINFORMATION);
            EnableWindow(hBtn, TRUE);
            break;
        }
        }
        break;
    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLOREDIT: {
        HDC hdc = (HDC)w;
        SetTextColor(hdc, RGB(255, 255, 255));
        SetBkMode(hdc, TRANSPARENT);
        return (INT_PTR)hbrBg;
    }
    case WM_CTLCOLORBTN: {
        HDC hdc = (HDC)w;
        SetTextColor(hdc, RGB(255, 255, 255));
        SetBkMode(hdc, OPAQUE);
        SetBkColor(hdc, RGB(45, 45, 48));
        return (INT_PTR)hbrBg;
    }
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    }
    return DefWindowProc(hwnd, msg, w, l);
}

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE, LPSTR, int cmdShow) {
    WNDCLASS wc = {};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.lpszClassName = L"Among Us Unlock All";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = CreateSolidBrush(RGB(32, 32, 32));
    RegisterClass(&wc);
    HWND hwnd = CreateWindowEx(
        0, wc.lpszClassName, L"Among Us Unlock All",
        WS_OVERLAPPEDWINDOW & ~WS_MAXIMIZEBOX & ~WS_SIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 400, 250,
        NULL, NULL, hInst, NULL
    );
    if (!hwnd) return 0;
    ShowWindow(hwnd, cmdShow);
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return 0;
}
