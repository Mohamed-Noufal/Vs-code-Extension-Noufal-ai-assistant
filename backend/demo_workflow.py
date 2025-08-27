#!/usr/bin/env python3
"""
Demo Workflow for Multi-Agent Development System
This script demonstrates how the three agents work together
"""

import asyncio
import json
from app.models.manager import ModelManager
from app.models.mistral import MistralPromptTemplate
from app.orchestrator.workflow import WorkflowManager


async def demo_simple_workflow():
    """Demonstrate a simple workflow with the three agents"""
    
    print("🚀 Multi-Agent Development System Demo")
    print("=" * 50)
    
    # Initialize the model manager
    print("\n1️⃣ Initializing AI Model Manager...")
    model_manager = ModelManager()
    await model_manager.initialize()
    print("✅ Model Manager ready!")
    
    # Initialize workflow manager
    print("\n2️⃣ Initializing Workflow Manager...")
    workflow_manager = WorkflowManager(model_manager)
    await workflow_manager.initialize()
    print("✅ Workflow Manager ready!")
    
    # Demo user request
    user_request = "Create a simple Python calculator with basic operations"
    print(f"\n🎯 User Request: {user_request}")
    print("-" * 50)
    
    # Step 1: Q&A Intake Agent
    print("\n🤖 Q&A Intake Agent Analysis:")
    qa_prompt = MistralPromptTemplate.format_qa_prompt(user_request)
    print("📝 Generated Prompt:")
    print(qa_prompt[:200] + "..." if len(qa_prompt) > 200 else qa_prompt)
    
    # Simulate Q&A agent response
    qa_response = await model_manager.generate(qa_prompt, max_tokens=300)
    print(f"\n💬 Q&A Agent Response:")
    print(qa_response['text'][:300] + "..." if len(qa_response['text']) > 300 else qa_response['text'])
    
    # Step 2: Manager/Planner Agent
    print("\n📋 Manager/Planner Agent Planning:")
    manager_prompt = MistralPromptTemplate.format_manager_prompt(user_request)
    print("📝 Generated Prompt:")
    print(manager_prompt[:200] + "..." if len(manager_prompt) > 200 else manager_prompt)
    
    # Simulate manager agent response
    manager_response = await model_manager.generate(manager_prompt, max_tokens=400)
    print(f"\n📊 Manager Agent Plan:")
    print(manager_response['text'][:400] + "..." if len(manager_response['text']) > 400 else manager_response['text'])
    
    # Step 3: Code Agent
    print("\n💻 Code Agent Implementation:")
    task_details = "Implement a Python calculator class with add, subtract, multiply, divide methods"
    project_context = "Simple command-line calculator application"
    code_prompt = MistralPromptTemplate.format_code_prompt(task_details, project_context)
    print("📝 Generated Prompt:")
    print(code_prompt[:200] + "..." if len(code_prompt) > 200 else code_prompt)
    
    # Simulate code agent response
    code_response = await model_manager.generate(code_prompt, max_tokens=500)
    print(f"\n🔧 Code Agent Implementation:")
    print(code_response['text'][:500] + "..." if len(code_response['text']) > 500 else code_response['text'])
    
    # Extract code blocks
    code_blocks = MistralPromptTemplate.extract_code_from_response(code_response['text'])
    if code_blocks:
        print(f"\n📦 Extracted Code Blocks ({len(code_blocks)}):")
        for i, block in enumerate(code_blocks, 1):
            print(f"\n--- Block {i} ({block['language']}) ---")
            print(block['code'])
    
    # Step 4: Workflow Summary
    print("\n🎉 Workflow Complete!")
    print("=" * 50)
    print("📊 Summary:")
    print(f"   • User Request: {user_request}")
    print(f"   • Q&A Analysis: Completed")
    print(f"   • Planning: Completed")
    print(f"   • Implementation: Completed")
    print(f"   • Code Blocks: {len(code_blocks)} extracted")
    
    # Cleanup
    await workflow_manager.shutdown()
    await model_manager.shutdown()
    print("\n🧹 Cleanup completed!")


async def demo_interactive_workflow():
    """Interactive demo where user can input their own requests"""
    
    print("\n🎮 Interactive Demo Mode")
    print("=" * 30)
    
    while True:
        try:
            user_input = input("\n💭 Enter your development request (or 'quit' to exit): ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input.strip():
                print("⚠️ Please enter a valid request")
                continue
            
            print(f"\n🚀 Processing: {user_input}")
            print("-" * 40)
            
            # Initialize model manager for this request
            model_manager = ModelManager()
            await model_manager.initialize()
            
            # Generate response using the intake agent prompt
            prompt = MistralPromptTemplate.format_qa_prompt(user_input)
            response = await model_manager.generate(prompt, max_tokens=400)
            
            print("🤖 AI Agent Response:")
            print(response['text'])
            
            # Ask if user wants to see code generation
            code_choice = input("\n💻 Would you like to see code generation? (y/n): ")
            
            if code_choice.lower() in ['y', 'yes']:
                print("\n🔧 Generating code...")
                code_prompt = MistralPromptTemplate.format_code_prompt(user_input, "General development project")
                code_response = await model_manager.generate(code_prompt, max_tokens=600)
                
                print("💻 Generated Code:")
                print(code_response['text'])
                
                # Extract and show code blocks
                code_blocks = MistralPromptTemplate.extract_code_from_response(code_response['text'])
                if code_blocks:
                    print(f"\n📦 Extracted Code Blocks ({len(code_blocks)}):")
                    for i, block in enumerate(code_blocks, 1):
                        print(f"\n--- Block {i} ({block['language']}) ---")
                        print(block['code'])
            
            await model_manager.shutdown()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("🔄 Continuing with demo...")


async def main():
    """Main demo function"""
    print("🎯 Multi-Agent Development System Demo")
    print("Choose demo mode:")
    print("1. Simple workflow demonstration")
    print("2. Interactive mode (your own requests)")
    
    try:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            await demo_simple_workflow()
        elif choice == "2":
            await demo_interactive_workflow()
        else:
            print("❌ Invalid choice. Running simple demo...")
            await demo_simple_workflow()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())






