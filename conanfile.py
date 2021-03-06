from conans import ConanFile, CMake, tools
import os

class ZMQConan(ConanFile):
    """ ZMQ is a network, sockets on steroids library. 
    Safe for use in commercial applications LGPL v3 with static linking exception
    """
    name = "libzmq"
    version = "4.2.0"
    version_flat = "4_2_0"
    license = "LGPL"
    url = "https://github.com/memsharded/conan-zmq.git"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    exports = "FindZeroMQ.cmake"
    generators = "cmake"

    def source(self):
        self.run("git clone https://github.com/zeromq/libzmq.git")
        self.run("cd libzmq && git checkout v4.2.0")
        tools.replace_in_file("libzmq/CMakeLists.txt", "project (ZeroMQ)", """project (ZeroMQ)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
""")
          
    def build(self):
        cmake = CMake(self.settings)
        self.run('cmake libzmq %s -DZMQ_BUILD_TESTS=OFF -DZMQ_BUILD_FRAMEWORK=OFF' % cmake.command_line)
        self.run("cmake --build . %s" % cmake.build_config)

    def package(self):
        self.copy_headers("*", "libzmq/include")
        self.copy("FindZeroMQ.cmake")
        if not self.options.shared:
            self.copy("*libzmq*-mt-s*.lib", "lib", "lib", keep_path=False)
            self.copy("*.a", "lib", "lib", keep_path=False)  # Linux
        else:
            self.copy("*libzmq*-mt-%s.lib" % self.version_flat, "lib", "lib", keep_path=False)
            self.copy("*libzmq*-mt-gd-%s.lib" % self.version_flat, "lib", "lib", keep_path=False)
            self.copy("*.dll", "bin", "bin", keep_path=False)
            self.copy("*.dylib", "lib", "lib", keep_path=False)
            self.copy("libzmq.so*", "lib", "lib", keep_path=False)  # Linux

    def package_info(self):
        if self.settings.os != "Windows":
            self.cpp_info.libs = ["zmq-static"] if not self.options.shared else ["zmq"]
        else:
            ver = ""
            if self.settings.compiler == "Visual Studio":
                if str(self.settings.compiler.version) in ["11", "12", "14"]:  
                    ver = "-v%s0" % self.settings.compiler.version
                else:
                    ver = "-"
            static, stat_fix = ("-static", "s") if not self.options.shared else ("", "")
            debug_fix = "gd" if self.settings.build_type == "Debug" else ""
            fix = ("-%s%s" % (stat_fix, debug_fix)) if stat_fix or debug_fix else ""
            self.cpp_info.libs = ["libzmq%s%s-mt%s-%s" % (static, ver, fix, self.version_flat)]

        if not self.options.shared:
            if self.settings.compiler == "Visual Studio":
                self.cpp_info.libs.extend(["ws2_32", "wsock32","Iphlpapi"])
            self.cpp_info.defines = ["ZMQ_STATIC"]

            if not self.settings.os == "Windows":
                self.cpp_info.cppflags = ["-pthread"]
        
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "dl", "rt"])
