package com.codearchaeologist.tracer;

import net.bytebuddy.agent.builder.AgentBuilder;
import net.bytebuddy.asm.Advice;
import net.bytebuddy.description.type.TypeDescription;
import net.bytebuddy.dynamic.DynamicType;
import net.bytebuddy.matcher.ElementMatchers;
import net.bytebuddy.utility.JavaModule;

import java.lang.instrument.Instrumentation;
import java.lang.reflect.Method;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.io.FileWriter;
import java.io.IOException;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

/**
 * Code Archaeologist - Java ByteBuddy Agent
 * Week 3: Java method tracing for call graph analysis
 * 
 * Usage: java -javaagent:java-tracer.jar -jar your-app.jar
 */
public class CodeArchaeologistAgent {
    
    // Trace storage
    private static final List<TraceEvent> events = Collections.synchronizedList(new ArrayList<>());
    private static final Map<String, MethodInfo> methodRegistry = new ConcurrentHashMap<>();
    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();
    private static String outputFile = "java_trace.json";
    private static String packageFilter = null;  // Filter by package
    
    public static void premain(String agentArgs, Instrumentation inst) {
        System.out.println("🔍 Code Archaeologist Java Agent - Week 3");
        
        // Parse arguments
        if (agentArgs != null) {
            for (String arg : agentArgs.split(",")) {
                if (arg.startsWith("output=")) {
                    outputFile = arg.substring(7);
                } else if (arg.startsWith("package=")) {
                    packageFilter = arg.substring(8);
                }
            }
        }
        
        System.out.println("📁 Output: " + outputFile);
        if (packageFilter != null) {
            System.out.println("📦 Package filter: " + packageFilter);
        }
        
        // Install shutdown hook to write trace
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            writeTraceToFile();
        }));
        
        // Set up ByteBuddy agent
        AgentBuilder agentBuilder = new AgentBuilder.Default()
            .with(AgentBuilder.Listener.StreamWriting.toSystemOut())
            .with(AgentBuilder.RedefinitionStrategy.RETRANSFORMATION);
        
        // Apply package filter if specified
        if (packageFilter != null) {
            agentBuilder = agentBuilder.type(
                ElementMatchers.nameStartsWith(packageFilter)
            );
        }
        
        agentBuilder
            .transform((builder, typeDescription, classLoader, module, protectionDomain) -> {
                return builder
                    .method(ElementMatchers.any())
                    .intercept(Advice.to(MethodTracer.class));
            })
            .installOn(inst);
        
        System.out.println("✅ Java agent installed. Tracing method calls...");
    }
    
    /**
     * ByteBuddy Advice for method entry/exit tracing
     */
    public static class MethodTracer {
        
        @Advice.OnMethodEnter
        public static void onEnter(
                @Advice.Origin Method method,
                @Advice.This(optional = true) Object self,
                @Advice.AllArguments Object[] args) {
            
            long timestamp = System.nanoTime();
            String className = method.getDeclaringClass().getName();
            String methodName = method.getName();
            String signature = className + "." + methodName;
            
            // Store method info
            MethodInfo info = new MethodInfo(
                signature,
                className,
                methodName,
                method.getParameterTypes().length,
                method.getModifiers()
            );
            methodRegistry.put(signature, info);
            
            // Create trace event
            TraceEvent event = new TraceEvent(
                UUID.randomUUID().toString(),
                "call",
                signature,
                className.replace('.', '/') + ".java",
                0,  // Line number not available via reflection
                getArgumentsString(args),
                Thread.currentThread().getId(),
                timestamp,
                "java"
            );
            
            events.add(event);
            
            // Print for debugging
            if (events.size() % 100 == 0) {
                System.out.println("📊 Collected " + events.size() + " events");
            }
        }
        
        @Advice.OnMethodExit(onThrowable = Throwable.class)
        public static void onExit(
                @Advice.Origin Method method,
                @Advice.Return(optional = true) Object result,
                @Advice.Thrown Throwable throwable) {
            
            long timestamp = System.nanoTime();
            String className = method.getDeclaringClass().getName();
            String methodName = method.getName();
            String signature = className + "." + methodName;
            
            String eventType = (throwable != null) ? "exception" : "return";
            String returnValue = (throwable != null) 
                ? throwable.getClass().getName() 
                : (result != null ? result.toString() : "void");
            
            TraceEvent event = new TraceEvent(
                UUID.randomUUID().toString(),
                eventType,
                signature,
                className.replace('.', '/') + ".java",
                0,
                returnValue,
                Thread.currentThread().getId(),
                timestamp,
                "java"
            );
            
            events.add(event);
        }
        
        private static String getArgumentsString(Object[] args) {
            if (args == null || args.length == 0) return "()";
            StringBuilder sb = new StringBuilder("(");
            for (int i = 0; i < args.length; i++) {
                if (i > 0) sb.append(", ");
                sb.append(args[i] != null ? args[i].toString() : "null");
            }
            sb.append(")");
            return sb.toString();
        }
    }
    
    /**
     * Trace event matching Python TraceEvent format
     */
    public static class TraceEvent {
        public String id;
        public String event;  // "call", "return", "exception", "line"
        public String function;
        public String filename;
        public int lineno;
        public String code;
        public Long parent;   // Parent call ID
        public String language;
        
        // Week 2: Variable tracking (not available in Java without JVMTI)
        public List<String> reads = new ArrayList<>();
        public List<String> writes = new ArrayList<>();
        
        // Java specific
        public long thread_id;
        public long timestamp_ns;
        
        public TraceEvent(String id, String event, String function, 
                         String filename, int lineno, String code,
                         long thread_id, long timestamp, String language) {
            this.id = id;
            this.event = event;
            this.function = function;
            this.filename = filename;
            this.lineno = lineno;
            this.code = code;
            this.thread_id = thread_id;
            this.timestamp_ns = timestamp;
            this.language = language;
        }
    }
    
    /**
     * Method metadata
     */
    public static class MethodInfo {
        public String signature;
        public String className;
        public String methodName;
        public int parameterCount;
        public int modifiers;
        
        public MethodInfo(String signature, String className, String methodName,
                         int parameterCount, int modifiers) {
            this.signature = signature;
            this.className = className;
            this.methodName = methodName;
            this.parameterCount = parameterCount;
            this.modifiers = modifiers;
        }
    }
    
    /**
     * Write trace to JSON file (matching Python format)
     */
    private static void writeTraceToFile() {
        System.out.println("💾 Writing trace to: " + outputFile);
        
        Map<String, Object> traceOutput = new HashMap<>();
        traceOutput.put("language", "java");
        traceOutput.put("version", "3.0.0");
        traceOutput.put("week", 3);
        traceOutput.put("event_count", events.size());
        traceOutput.put("method_count", methodRegistry.size());
        traceOutput.put("timestamp", Instant.now().toString());
        traceOutput.put("events", events);
        traceOutput.put("methods", new ArrayList<>(methodRegistry.values()));
        
        try (FileWriter writer = new FileWriter(outputFile)) {
            gson.toJson(traceOutput, writer);
            System.out.println("✅ Trace written: " + events.size() + " events");
        } catch (IOException e) {
            System.err.println("❌ Failed to write trace: " + e.getMessage());
        }
    }
    
    /**
     * Get current events (for programmatic access)
     */
    public static List<TraceEvent> getEvents() {
        return new ArrayList<>(events);
    }
    
    /**
     * Clear events
     */
    public static void clearEvents() {
        events.clear();
        methodRegistry.clear();
    }
}
